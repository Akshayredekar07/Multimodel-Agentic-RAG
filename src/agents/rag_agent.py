import sqlite3
from pathlib import Path
from typing import Annotated, Literal, TypedDict

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from agents.prompts import AGENT_SYSTEM_MESSAGE
from model_providers import LLMFactory
from retrieval.retriever import build_retrieval_tools
from retrieval.vector_store import create_vectorstore
from dotenv import load_dotenv

load_dotenv()

class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


class RAGAgent:
    def __init__(self, factory: LLMFactory, llm: BaseChatModel, vectorstore, sqlite_path: str = "agent_memory.db") -> None:
        self.factory = factory
        self.llm = llm
        self.vectorstore = vectorstore
        self.tools = build_retrieval_tools(vectorstore)
        self.tool_node = ToolNode(self.tools)
        self.short_mem = InMemorySaver()
        self.sqlite_conn = sqlite3.connect(sqlite_path, check_same_thread=False)
        self.long_mem = SqliteSaver(self.sqlite_conn)
        self.agent_graph = self.build_graph(checkpointer=self.short_mem)
        self.agent_graph_persistent = self.build_graph(checkpointer=self.long_mem)

    def make_agent_node(self, llm: BaseChatModel):
        llm_with_tools = llm.bind_tools(self.tools)

        def agent(state: State) -> State:
            messages = state["messages"]
            if not messages or messages[0].type != "system":
                messages = [AGENT_SYSTEM_MESSAGE] + list(messages)
            return {"messages": [llm_with_tools.invoke(messages)]}

        return agent

    @staticmethod
    def route_agent(state: State) -> Literal["tools", "__end__"]:
        last = state["messages"][-1]
        if isinstance(last, AIMessage) and hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
        return "__end__"

    def build_graph(self, llm: BaseChatModel | None = None, checkpointer=None):
        active_llm = llm or self.llm
        graph = StateGraph(State)
        graph.add_node("agent", self.make_agent_node(active_llm))
        graph.add_node("tools", self.tool_node)
        graph.add_edge(START, "agent")
        graph.add_conditional_edges("agent", self.route_agent, {"tools": "tools", "__end__": END})
        graph.add_edge("tools", "agent")

        compiled_graph = graph.compile(checkpointer=checkpointer)
        return compiled_graph

    def create_provider_graph(self, provider: str, model_name: str | None = None, checkpointer=None, **kwargs):
        provider_llm = self.factory.get_llm(provider=provider, model_name=model_name, **kwargs)
        return self.build_graph(llm=provider_llm, checkpointer=checkpointer or InMemorySaver())

    def run(self, query: str, thread_id: str = "default", graph=None, verbose: bool = True) -> str:
        active_graph = graph or self.agent_graph
        config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
        final_answer: str = ""

        for event in active_graph.stream({"messages": [HumanMessage(content=query)]}, config, stream_mode="values"):
            last = event["messages"][-1]
            if isinstance(last, AIMessage) and last.content:
                final_answer = last.content if isinstance(last.content, str) else str(last.content)
        return final_answer

    def show_thread(self, thread_id: str, graph=None) -> None:
        active_graph = graph or self.agent_graph
        snapshot = active_graph.get_state({"configurable": {"thread_id": thread_id}})
        _ = snapshot


def create_rag_agent(provider: str = "nebius", model_name: str = "MiniMaxAI/MiniMax-M2.5", temperature: float = 0.5, sqlite_path: str = "agent_memory.db") -> RAGAgent:
    factory = LLMFactory()
    _, vectorstore = create_vectorstore()
    llm = factory.get_llm(provider=provider, model_name=model_name, temperature=temperature)
    return RAGAgent(factory=factory, llm=llm, vectorstore=vectorstore, sqlite_path=sqlite_path)
