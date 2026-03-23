# # main.py
# import base64
# from pathlib import Path
# from dotenv import load_dotenv
# from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
# from langchain_groq import ChatGroq
# from langchain_core.messages import HumanMessage
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.output_parsers import StrOutputParser

# from chunking import partition_document, process_images, process_tables, process_text_chunks
# from vectorstore import build_vectorstore, save_vectorstore, load_vectorstore, hybrid_search

# load_dotenv()

# BASE_DIR      = Path(__file__).resolve().parent.parent
# VECTORDB_PATH = str(BASE_DIR / "data" / "vectordb")
# PDF_PATH      = str(BASE_DIR / "data" / "raw" / "attention.pdf")

# embeddings = NVIDIAEmbeddings(model="baai/bge-m3")
# text_llm   = ChatGroq(model="openai/gpt-oss-120b")
# vision_llm = ChatGroq(model="meta-llama/llama-4-scout-17b-16e-instruct")


# def build_pipeline():
#     raw_chunks  = partition_document(PDF_PATH)
#     images      = process_images(raw_chunks, vision_llm)
#     tables      = process_tables(raw_chunks, text_llm)
#     text_chunks = process_text_chunks(raw_chunks)
#     all_chunks  = images + tables + text_chunks
#     vs          = build_vectorstore(all_chunks, embeddings)
#     save_vectorstore(vs, VECTORDB_PATH)
#     return vs


# def load_pipeline():
#     return load_vectorstore(VECTORDB_PATH, embeddings)


# def answer_from_text(query: str, docs: list) -> str:
#     context = "\n\n".join(
#         f"[page={d.metadata.get('page')} | {d.metadata.get('content_type')}]\n{d.page_content}"
#         for d, _ in docs
#     )
#     prompt = ChatPromptTemplate.from_messages([
#         ("system",
#          "Answer using only the context below.\n"
#          "If not found say 'Not found in document'.\n\nContext:\n{context}"),
#         ("human", "{question}"),
#     ])
#     return (prompt | text_llm | StrOutputParser()).invoke(
#         {"context": context, "question": query}
#     )


# def answer_from_images(query: str, image_docs: list) -> str:
#     if not image_docs:
#         return ""
#     answers = []
#     for doc in image_docs:
#         path = doc.metadata.get("image_path")
#         if not path or not Path(path).exists():
#             continue
#         with open(path, "rb") as f:
#             b64 = base64.b64encode(f.read()).decode("utf-8")
#         ext  = Path(path).suffix.lower().replace(".", "")
#         mime = f"image/{'jpeg' if ext in ['jpg','jpeg'] else ext}"
#         resp = vision_llm.invoke([HumanMessage(content=[
#             {"type": "text",      "text": f"Page {doc.metadata.get('page')} of Attention Is All You Need paper. {query}"},
#             {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
#         ])])
#         answers.append(f"[image page={doc.metadata.get('page')}]: {resp.content}")
#     return "\n\n".join(answers) if answers else ""


# def multimodal_chat(query: str, vectorstore, image_vectorstore, k: int = 6) -> None:
#     print(f"\n{'='*60}")
#     print(f"Q: {query}")
#     print(f"{'='*60}")

#     text_results  = hybrid_search(vectorstore, query, k=k)
#     image_results = hybrid_search(image_vectorstore, query, k=99)  # all images

#     text_answer  = answer_from_text(query, text_results)
#     vision_answer = answer_from_images(query, [d for d, _ in image_results])

#     print(f"\n--- text answer ---")
#     print(text_answer)

#     if vision_answer and vision_answer.strip():
#         print(f"\n--- vision answer ---")
#         print(vision_answer)


# if __name__ == "__main__":
#     from langchain_community.vectorstores import FAISS
#     from langchain_core.documents import Document

#     vectordb = Path(VECTORDB_PATH)
#     if not vectordb.exists() or not (vectordb / "index.faiss").exists():
#         print("Building vectorstore...")
#         vectorstore = build_pipeline()
#     else:
#         print("Loading vectorstore...")
#         vectorstore = load_pipeline()

#     # build image-only store for dedicated image retrieval
#     all_docs = [
#         vectorstore.docstore.search(doc_id)
#         for doc_id in vectorstore.index_to_docstore_id.values()
#     ]
#     image_docs = [d for d in all_docs if isinstance(d, Document) and d.metadata.get("content_type") == "image"]
#     print(f"Image docs in separate store: {len(image_docs)}")

#     image_vectorstore = FAISS.from_documents(image_docs, embeddings) if image_docs else vectorstore

#     questions = [
#         "What is the transformer architecture?",
#         "Explain positional encoding",
#         "What is Multi-Head Attention",
#     ]

#     for q in questions:
#         multimodal_chat(q, vectorstore, image_vectorstore, k=6)


from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
import base64
from dotenv import load_dotenv
load_dotenv()

vision_llm = ChatGroq(model="meta-llama/llama-4-scout-17b-16e-instruct")

with open("extracted_images/figure-3-1.jpg", "rb") as f:
    b64 = base64.b64encode(f.read()).decode("utf-8")

resp = vision_llm.invoke([HumanMessage(content=[
    {"type": "text",      "text": "Describe this diagram in one sentence."},
    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
])])
print(resp.content)