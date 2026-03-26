import logging
import sqlite3
from typing import Annotated, Literal, TypedDict

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from agents.prompts import (
    AGENT_SYSTEM_MESSAGE,
    ANSWER_SYSTEM_MESSAGE,
    GRADE_SYSTEM_MESSAGE,
    REWRITE_SYSTEM_MESSAGE,
)
from model_providers import LLMFactory
from retrieval.retriever import build_retrieval_tools
from retrieval.vector_store import create_vectorstore


class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    query: str
    retrieved_docs: str
    relevance: str
    final_answer: str


class RAGAgent:
    def __init__(
        self,
        factory: LLMFactory,
        llm: BaseChatModel,
        vectorstore,
        sqlite_path: str = "agent_memory.db",
        logger: logging.Logger | None = None,
    ) -> None:
        self.factory = factory
        self.llm = llm
        self.vectorstore = vectorstore
        self.log = logger or logging.getLogger("rag-agent")
        self.tools = build_retrieval_tools(vectorstore)
        self.tool_node = ToolNode(self.tools)
        self.short_mem = InMemorySaver()
        self.sqlite_conn = sqlite3.connect(sqlite_path, check_same_thread=False)
        self.long_mem = SqliteSaver(self.sqlite_conn)
        self.agent_graph = self.build_graph(checkpointer=self.short_mem)
        self.agent_graph_persistent = self.build_graph(checkpointer=self.long_mem)

        self.log.info("Available providers: %s", self.factory.available_providers)
        self.log.info("Tools: %s", [tool.name for tool in self.tools])
        self.log.info("Graphs compiled")

    def _make_rewrite_node(self, llm: BaseChatModel):
        def rewrite(state: State) -> State:
            last_human = next(
                (message for message in reversed(state["messages"]) if isinstance(message, HumanMessage)),
                None,
            )
            if not last_human:
                return {
                    "query": "",
                    "messages": [],
                    "retrieved_docs": "",
                    "relevance": "",
                    "final_answer": "",
                }

            rewritten = llm.invoke(
                [
                    REWRITE_SYSTEM_MESSAGE,
                    HumanMessage(content=last_human.content),
                ]
            )
            rewritten_content = rewritten.content if isinstance(rewritten.content, str) else str(rewritten.content)
            self.log.info("Rewrite: %r -> %r", last_human.content[:60], rewritten_content[:60])
            return {
                "query": rewritten_content.strip(),
                "messages": [],
                "retrieved_docs": "",
                "relevance": "",
                "final_answer": "",
            }

        return rewrite

    def _make_agent_node(self, llm: BaseChatModel):
        llm_with_tools = llm.bind_tools(self.tools)

        def agent(state: State) -> State:
            messages = state["messages"]
            if not messages or messages[0].type != "system":
                messages = [AGENT_SYSTEM_MESSAGE] + list(messages)
            return {
                "messages": [llm_with_tools.invoke(messages)],
                "query": state.get("query", ""),
                "retrieved_docs": state.get("retrieved_docs", ""),
                "relevance": state.get("relevance", ""),
                "final_answer": state.get("final_answer", ""),
            }

        return agent

    def _make_grade_node(self, llm: BaseChatModel):
        def grade(state: State) -> State:
            context = " ".join(
                message.content
                for message in state["messages"]
                if isinstance(message, ToolMessage) and isinstance(message.content, str)
            )
            if not context:
                return {
                    "relevance": "irrelevant",
                    "retrieved_docs": "",
                    "messages": state.get("messages", []),
                    "query": state.get("query", ""),
                    "final_answer": state.get("final_answer", ""),
                }

            verdict = llm.invoke(
                [
                    GRADE_SYSTEM_MESSAGE,
                    HumanMessage(
                        content=f"Query: {state.get('query', '')}\n\nContext: {context[:1000]}"
                    ),
                ]
            )
            verdict_text = verdict.content if isinstance(verdict.content, str) else str(verdict.content).strip().lower()
            verdict_text = verdict_text.strip().lower()
            label = "relevant" if verdict_text == "relevant" else "irrelevant"
            self.log.info("Relevance: %s", label)
            return {
                "relevance": label,
                "retrieved_docs": context,
                "messages": state.get("messages", []),
                "query": state.get("query", ""),
                "final_answer": state.get("final_answer", ""),
            }

        return grade

    def _make_answer_node(self, llm: BaseChatModel):
        def answer(state: State) -> State:
            response = llm.invoke(
                [
                    ANSWER_SYSTEM_MESSAGE,
                    HumanMessage(
                        content=(
                            f"Query: {state.get('query', '')}\n\n"
                            f"Context:\n{state.get('retrieved_docs', 'No context.')}"
                        )
                    ),
                ]
            )
            content = response.content if isinstance(response.content, str) else str(response.content)
            self.log.info("Answer produced (%d chars)", len(content))
            return {
                "final_answer": content,
                "messages": [response],
                "query": state.get("query", ""),
                "retrieved_docs": state.get("retrieved_docs", ""),
                "relevance": state.get("relevance", ""),
            }

        return answer

    @staticmethod
    def route_agent(state: State) -> Literal["tools", "__end__"]:
        last = state["messages"][-1]
        if isinstance(last, AIMessage) and hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
        return "__end__"

    @staticmethod
    def route_grade(state: State) -> Literal["answer", "agent"]:
        return "answer" if state.get("relevance") == "relevant" else "agent"

    def build_graph(self, llm: BaseChatModel | None = None, checkpointer=None):
        active_llm = llm or self.llm
        graph = StateGraph(State)
        graph.add_node("rewrite", self._make_rewrite_node(active_llm))
        graph.add_node("agent", self._make_agent_node(active_llm))
        graph.add_node("tools", self.tool_node)
        graph.add_node("grade", self._make_grade_node(active_llm))
        graph.add_node("answer", self._make_answer_node(active_llm))

        graph.add_edge(START, "rewrite")
        graph.add_edge("rewrite", "agent")
        graph.add_conditional_edges("agent", self.route_agent, {"tools": "tools", "__end__": END})
        graph.add_edge("tools", "grade")
        graph.add_conditional_edges("grade", self.route_grade, {"answer": "answer", "agent": "agent"})
        graph.add_edge("answer", END)

        return graph.compile(checkpointer=checkpointer)

    def create_provider_graph(
        self,
        provider: str,
        model_name: str | None = None,
        checkpointer=None,
        **kwargs,
    ):
        provider_llm = self.factory.get_llm(provider=provider, model_name=model_name, **kwargs)
        return self.build_graph(
            llm=provider_llm,
            checkpointer=checkpointer or InMemorySaver(),
        )

    def run(
        self,
        query: str,
        thread_id: str = "default",
        graph=None,
        verbose: bool = True,
    ) -> str:
        active_graph = graph or self.agent_graph
        config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
        final_answer: str = ""

        if verbose:
            print(f"\n{'=' * 65}")
            print(f"USER [{thread_id}]: {query}")
            print(f"{'-' * 65}")

        for event in active_graph.stream(
            {
                "messages": [HumanMessage(content=query)],
                "query": "",
                "retrieved_docs": "",
                "relevance": "",
                "final_answer": "",
            },
            config,
            stream_mode="values",
        ):
            last = event["messages"][-1]

            if verbose:
                if hasattr(last, "tool_calls") and last.tool_calls:
                    for tool_call in last.tool_calls:
                        print(f"  -> tool call  : {tool_call['name']}({tool_call.get('args', {})})")
                elif isinstance(last, ToolMessage):
                    preview = (last.content or "")[:180]
                    suffix = "..." if len(last.content or "") > 180 else ""
                    print(f"  <- tool result: {preview}{suffix}")
                elif isinstance(last, AIMessage) and last.content:
                    final_answer = last.content if isinstance(last.content, str) else str(last.content)

            if event.get("final_answer"):
                final_answer = str(event["final_answer"])

        if verbose:
            print(f"\nAGENT: {final_answer}")
            print(f"{'=' * 65}\n")

        return final_answer

    def show_thread(self, thread_id: str, graph=None) -> None:
        active_graph = graph or self.agent_graph
        snapshot = active_graph.get_state({"configurable": {"thread_id": thread_id}})
        print(f"\nThread '{thread_id}':")
        for message in snapshot.values.get("messages", []):
            role = message.__class__.__name__
            content = str(message.content)[:120]
            print(f"  [{role:<18}] {content}")


def create_rag_agent(
    provider: str = "nebius",
    model_name: str = "MiniMaxAI/MiniMax-M2.5",
    temperature: float = 0.5,
    sqlite_path: str = "agent_memory.db",
    logger: logging.Logger | None = None,
) -> RAGAgent:
    active_logger = logger or logging.getLogger("rag-agent")
    factory = LLMFactory()
    _, vectorstore = create_vectorstore(logger=active_logger)
    llm = factory.get_llm(provider=provider, model_name=model_name, temperature=temperature)
    return RAGAgent(
        factory=factory,
        llm=llm,
        vectorstore=vectorstore,
        sqlite_path=sqlite_path,
        logger=active_logger,
    )
