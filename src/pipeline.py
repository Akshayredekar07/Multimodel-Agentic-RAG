import logging

from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver

from agents.rag_agent import create_rag_agent


load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")


def main() -> None:
    agent = create_rag_agent()

    agent.run("What is self-attention in the Transformer architecture?", thread_id="t1")
    agent.run("Explain multi-head attention.", thread_id="t2")
    agent.run("How is it different from what you just explained?", thread_id="t2")
    agent.run("Which page covered that?", thread_id="t2")
    agent.run("What does the model architecture diagram show?", thread_id="t3")
    agent.run("Show me all tables about training results.", thread_id="t4")
    agent.run("Explain positional encoding.", thread_id="persist-1", graph=agent.agent_graph_persistent)
    agent.show_thread("t2")

    groq_graph = agent.create_provider_graph(provider="groq", model_name="llama-3.3-70b-versatile", temperature=0.1, checkpointer=InMemorySaver())
    agent.run("What is layer normalisation used for in Transformers?", thread_id="groq-1", graph=groq_graph)


if __name__ == "__main__":
    main()
