from agents.rag_agent import create_rag_agent

rag_agent = create_rag_agent()
agent = rag_agent.build_graph(checkpointer=None)
