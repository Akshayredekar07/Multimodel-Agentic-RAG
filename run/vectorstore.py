from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document


def build_vectorstore(all_chunks: list, embeddings) -> FAISS:
    docs = [
        Document(
            page_content=chunk["content"],
            metadata={
                "content_type" : chunk.get("content_type"),
                "page"         : chunk.get("page"),
                "filename"     : chunk.get("filename"),
                "caption"      : chunk.get("caption", ""),
                "table_html"   : chunk.get("table_html", ""),
            }
        )
        for chunk in all_chunks
        if chunk.get("content", "").strip()
    ]

    from collections import Counter
    print(f"Total docs: {len(docs)}")
    print(Counter(d.metadata["content_type"] for d in docs))

    return FAISS.from_documents(docs, embeddings)


def save_vectorstore(vectorstore: FAISS, path: str) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(path)
    print(f"Saved vectorstore to: {path}")


def load_vectorstore(path: str, embeddings) -> FAISS:
    vs = FAISS.load_local(path, embeddings, allow_dangerous_deserialization=True)
    print(f"Loaded vectorstore | size: {vs.index.ntotal}")
    return vs



def keyword_search(vectorstore: FAISS, query: str, k: int = 5) -> list:
    # FAISS has no native keyword search — filter by content type instead
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k}
    )
    docs = retriever.invoke(query)
    return [(doc, None) for doc in docs]


# vectorstore.py — update semantic_search
def semantic_search(vectorstore: FAISS, query: str, k: int = 5) -> list:
    results = vectorstore.similarity_search_with_score(query, k=k)
    return results


def hybrid_search(vectorstore: FAISS, query: str, k: int = 5) -> list:
    # MMR gives more diverse results — better for short queries
    docs = vectorstore.max_marginal_relevance_search(query, k=k, fetch_k=k * 4)
    return [(doc, None) for doc in docs]