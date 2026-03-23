from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from vectorstore import hybrid_search, semantic_search, keyword_search

RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "Answer the question using only the context below.\n"
     "If the answer is not in the context, say 'Not found in document'.\n\n"
     "Context:\n{context}"),
    ("human", "{question}"),
])


def format_context(results: list) -> str:
    parts = []
    for doc, score in results:
        score_str = f"{score:.4f}" if score is not None else "n/a"
        parts.append(
            f"[{doc.metadata.get('content_type', 'text')} | "
            f"page={doc.metadata.get('page')} | score={score_str}]\n"
            f"{doc.page_content}"
        )
    return "\n\n---\n\n".join(parts)


def generate_rag_response(
    query: str,
    vectorstore,
    text_llm,
    search_type: str = "hybrid",
    k: int = 5,
) -> str:
    if search_type == "keyword":
        results = keyword_search(vectorstore, query, k=k)
    elif search_type == "semantic":
        results = semantic_search(vectorstore, query, k=k)
    else:
        results = hybrid_search(vectorstore, query, k=k)

    if not results:
        return "No relevant information found."

    context = format_context(results)
    chain   = RAG_PROMPT | text_llm | StrOutputParser()
    return chain.invoke({"context": context, "question": query})

