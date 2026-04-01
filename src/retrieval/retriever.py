from langchain_core.tools import tool
from qdrant_client.http.models import FieldCondition, Filter, MatchValue


def build_retrieval_tools(vectorstore):
    def _format_text_hits(hits, element_type: str | None = None) -> str:
        if not hits:
            if element_type:
                return f"No '{element_type}' elements found."
            return "No relevant text found."

        parts = []
        for doc, score in hits:
            page = doc.metadata.get("page", "?")
            dtype = element_type or doc.metadata.get("type", "text")
            parts.append(f"[Page {page} | {dtype} | score={score:.4f}]\n{doc.page_content}")
        return "\n\n---\n\n".join(parts)

    @tool
    def retrieve_text(query: str) -> str:
        """Retrieve the most relevant text chunks for a document question."""
        hits = vectorstore.similarity_search_with_score(query, k=4)
        return _format_text_hits(hits)

    @tool
    def retrieve_images(query: str) -> str:
        """Retrieve image-related results for questions about figures, diagrams, or charts."""
        hits = vectorstore.similarity_search_with_score(
            query,
            k=6,
            filter=Filter(
                must=[FieldCondition(key="metadata.type", match=MatchValue(value="image"))]
            ),
        )
        if not hits:
            return "No relevant images found."

        parts = []
        for doc, score in hits:
            page = doc.metadata.get("page", "?")
            path = doc.metadata.get("image_path", "unavailable")
            ocr = doc.page_content[:300]
            parts.append(f"[Image | Page {page} | score={score:.4f}]\npath={path}\nocr={ocr}")
        return "\n\n".join(parts)

    @tool
    def retrieve_by_type(element_type: str, query: str) -> str:
        """Retrieve results filtered to a specific document element type."""
        hits = vectorstore.similarity_search_with_score(
            query,
            k=4,
            filter=Filter(
                must=[
                    FieldCondition(
                        key="metadata.type",
                        match=MatchValue(value=element_type),
                    )
                ]
            ),
        )
        if not hits:
            return f"No '{element_type}' elements found for: {query}"
        return _format_text_hits(hits, element_type=element_type)

    return [retrieve_text, retrieve_images, retrieve_by_type]
