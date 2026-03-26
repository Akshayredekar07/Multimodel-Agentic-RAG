from __future__ import annotations

import base64
import difflib
import json
import mimetypes
import os
import re
import sys
import uuid
from functools import lru_cache
from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field


BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config import Config
from ingestion.chunkers import build_chunks
from model_providers import LLMFactory


load_dotenv()

APP_TITLE = "Multimodal RAG Workspace"
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))
DEFAULT_PROVIDER = os.getenv("MAIN_LLM_PROVIDER", "nebius")
DEFAULT_MODEL = os.getenv("MAIN_LLM_MODEL", "MiniMaxAI/MiniMax-M2.5")
DEFAULT_MODEL_LABEL = os.getenv(
    "MAIN_LLM_LABEL",
    DEFAULT_MODEL.rsplit("/", 1)[-1],
)
DEFAULT_TEMPERATURE = float(os.getenv("MAIN_LLM_TEMPERATURE", "0.2"))
ENABLE_IMAGE_SUMMARY = os.getenv("ENABLE_IMAGE_SUMMARY", "false").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
ENABLE_UNSTRUCTURED_IMAGE_OCR = os.getenv(
    "ENABLE_UNSTRUCTURED_IMAGE_OCR",
    "false",
).strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
UPLOAD_DIR = BASE_DIR / "uploaded_files"
TEXT_DIR = UPLOAD_DIR / "extracted_text"
CHUNKS_DIR = UPLOAD_DIR / "chunks"
MANIFEST_PATH = UPLOAD_DIR / "manifest.json"
SYSTEM_PROMPT = (
    "You are a helpful assistant. Answer only from the provided context. "
    "Format the response in Markdown. Start with exactly one H3 heading using ###. "
    "Use H4 headings with #### when helpful. Never use H1 or H2 headings. "
    "Do not expose raw retrieval labels like [file | chunk 6] in the answer body. "
    "Never start with phrases like 'Based on the provided context', "
    "'According to the context', or similar filler. "
    "Do not include a Sources section in the answer body. "
    "Do not mention chunk numbers, scores, or retrieval metadata in the main answer. "
    "If the context is not enough, say that clearly."
)

PROVIDER_KEY_MAP = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "gemini": "GOOGLE_API_KEY",
    "groq": "GROQ_API_KEY",
    "nvidia": "NVIDIA_API_KEY",
    "cerebras": "CEREBRAS_API_KEY",
    "nebius": "NEBIUS_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "huggingface": "HUGGINGFACE_API_KEY",
}

VISION_MODEL_CATALOG = [
    {
        "provider": "openai",
        "model_name": "gpt-4o",
        "api_key_name": "OPENAI_API_KEY",
    },
    {
        "provider": "nvidia",
        "model_name": "meta/llama-3.2-11b-vision-instruct",
        "api_key_name": "NVIDIA_API_KEY",
    },
]

STOPWORDS = {
    "a",
    "about",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "can",
    "do",
    "does",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "me",
    "of",
    "on",
    "or",
    "tell",
    "that",
    "the",
    "this",
    "to",
    "was",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
}

MODEL_CATALOG = [
    {
        "model_id": "default",
        "label": DEFAULT_MODEL_LABEL,
        "provider": DEFAULT_PROVIDER,
        "model_name": DEFAULT_MODEL,
        "api_key_name": PROVIDER_KEY_MAP.get(DEFAULT_PROVIDER),
    },
    {
        "model_id": "nebius_minimax_m2_5",
        "label": "MiniMax M2.5",
        "provider": "nebius",
        "model_name": "MiniMaxAI/MiniMax-M2.5",
        "api_key_name": "NEBIUS_API_KEY",
    },
    {
        "model_id": "openai_gpt_4o",
        "label": "GPT-4o",
        "provider": "openai",
        "model_name": "gpt-4o",
        "api_key_name": "OPENAI_API_KEY",
    },
    {
        "model_id": "groq_llama_3_3_70b",
        "label": "Llama 3.3 70B",
        "provider": "groq",
        "model_name": "llama-3.3-70b-versatile",
        "api_key_name": "GROQ_API_KEY",
    },
    {
        "model_id": "nvidia_llama_3_3_70b",
        "label": "NVIDIA Llama 3.3 70B",
        "provider": "nvidia",
        "model_name": "meta/llama-3.3-70b-instruct",
        "api_key_name": "NVIDIA_API_KEY",
    },
]

UPLOAD_DIR.mkdir(exist_ok=True)
TEXT_DIR.mkdir(exist_ok=True)
CHUNKS_DIR.mkdir(exist_ok=True)
if not MANIFEST_PATH.exists():
    MANIFEST_PATH.write_text("[]", encoding="utf-8")


class ChatTurn(BaseModel):
    role: str
    content: str


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    thread_id: str = "default"
    file_ids: list[str] = Field(default_factory=list)
    history: list[ChatTurn] = Field(default_factory=list)
    model_id: str | None = None
    search_all_files: bool = True


class ModelOption(BaseModel):
    model_id: str
    label: str
    provider: str
    model_name: str


class ModelsResponse(BaseModel):
    default_model_id: str
    models: list[ModelOption]


class SourceChunk(BaseModel):
    file_id: str
    filename: str
    chunk_index: int
    score: float
    content: str
    is_image: bool = False
    page_number: int | None = None


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]
    used_llm: bool


app = FastAPI(title=APP_TITLE)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def load_manifest() -> list[dict]:
    try:
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def save_manifest(records: list[dict]) -> None:
    MANIFEST_PATH.write_text(json.dumps(records, indent=2), encoding="utf-8")


def get_record_paths(record: dict) -> tuple[Path, Path, Path]:
    file_path = Path(record["path"])
    text_path = TEXT_DIR / f"{record['file_id']}.txt"
    chunks_path = CHUNKS_DIR / f"{record['file_id']}.json"
    return file_path, text_path, chunks_path


def find_record(file_id: str) -> dict | None:
    for record in load_manifest():
        if record["file_id"] == file_id:
            return record
    return None


def delete_record_files(record: dict) -> None:
    file_path, text_path, chunks_path = get_record_paths(record)
    for path in (file_path, text_path, chunks_path):
        if path.exists():
            path.unlink()


def sanitize_filename(filename: str) -> str:
    cleaned = Path(filename).name.strip()
    if not cleaned:
        return "upload.bin"
    return re.sub(r"[^A-Za-z0-9._-]+", "_", cleaned)


def detect_content_type(filename: str, content_type: str | None) -> str:
    if content_type:
        return content_type
    guessed, _ = mimetypes.guess_type(filename)
    return guessed or "application/octet-stream"


def is_image_type(filename: str, content_type: str | None) -> bool:
    resolved_type = detect_content_type(filename, content_type)
    return resolved_type.startswith("image/")


def get_vision_model_option() -> dict | None:
    for option in VISION_MODEL_CATALOG:
        key_name = option.get("api_key_name")
        if key_name and getattr(Config, key_name, None):
            return option
    return None


def build_image_data_url(file_path: Path) -> str:
    mime_type = detect_content_type(file_path.name, None)
    payload = base64.b64encode(file_path.read_bytes()).decode("utf-8")
    return f"data:{mime_type};base64,{payload}"


def extract_image_text_with_unstructured(file_path: Path) -> str:
    if not ENABLE_UNSTRUCTURED_IMAGE_OCR:
        return ""

    try:
        from unstructured.partition.image import partition_image

        elements = partition_image(filename=str(file_path), strategy="ocr_only")
        parts = []
        for element in elements:
            text = getattr(element, "text", "").strip()
            if text:
                parts.append(text)
        return "\n".join(parts).strip()
    except Exception:
        return ""


def summarize_image(file_path: Path, ocr_text: str = "") -> str:
    if not ENABLE_IMAGE_SUMMARY:
        return ""

    option = get_vision_model_option()
    if option is None:
        return ""

    try:
        llm = get_llm(
            option["provider"],
            option["model_name"],
            0.1,
        )
        image_data_url = build_image_data_url(file_path)
        prompt_parts = [
            "Create a retrieval-ready summary of this uploaded image.",
            "Mention the document type, key visible text, diagrams, labels, tables, or entities.",
            "Keep it concise and factual in 3 to 5 sentences.",
        ]
        if ocr_text.strip():
            prompt_parts.append(f"OCR text already extracted:\n{ocr_text[:1200]}")

        response = llm.invoke(
            [
                HumanMessage(
                    content=[
                        {"type": "text", "text": "\n\n".join(prompt_parts)},
                        {"type": "image_url", "image_url": {"url": image_data_url}},
                    ]
                )
            ]
        )
        content = str(response.content).strip() if hasattr(response, "content") else str(response).strip()
        return content
    except Exception:
        return ""


def should_generate_image_summary(ocr_text: str) -> bool:
    if not ENABLE_IMAGE_SUMMARY:
        return False
    if not ocr_text.strip():
        return True
    return len(extract_keywords(ocr_text)) < 6


def should_refresh_image_text(extracted_text: str) -> bool:
    text = extracted_text.strip()
    if not text:
        return True
    if text.startswith("Image file:"):
        return True
    return (
        "Image summary:" not in text
        and "OCR text:" not in text
        and len(text) < 80
    )


def extract_text(file_path: Path, content_type: str | None = None) -> str:
    suffix = file_path.suffix.lower()
    text_suffixes = {
        ".txt",
        ".md",
        ".py",
        ".json",
        ".yaml",
        ".yml",
        ".csv",
        ".html",
        ".htm",
        ".xml",
        ".log",
        ".rst",
    }

    try:
        if is_image_type(file_path.name, content_type):
            ocr_text = ""
            try:
                from PIL import Image
                import pytesseract

                image = Image.open(file_path)
                ocr_text = pytesseract.image_to_string(image).strip()
            except Exception:
                ocr_text = ""

            if not ocr_text:
                ocr_text = extract_image_text_with_unstructured(file_path)

            image_summary = ""
            if should_generate_image_summary(ocr_text):
                image_summary = summarize_image(file_path, ocr_text=ocr_text).strip()
            parts: list[str] = []
            if image_summary:
                parts.append(f"Image summary:\n{image_summary}")
            if ocr_text:
                parts.append(f"OCR text:\n{ocr_text}")
            if parts:
                return "\n\n".join(parts)
            return f"Image file: {file_path.stem}"

        if suffix in text_suffixes or (content_type or "").startswith("text/"):
            return file_path.read_text(encoding="utf-8", errors="ignore")

        if suffix == ".pdf":
            from pypdf import PdfReader

            reader = PdfReader(str(file_path))
            parts = []
            for index, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text() or ""
                if page_text.strip():
                    parts.append(f"[Page {index}]\n{page_text.strip()}")
            return "\n\n".join(parts)

        if suffix == ".docx":
            from docx import Document

            document = Document(str(file_path))
            return "\n".join(
                paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()
            )

        return file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def ensure_record_index(record: dict) -> dict:
    file_path, text_path, chunks_path = get_record_paths(record)

    if not file_path.exists():
        return record

    content_type = record.get("content_type")
    refresh_text = not text_path.exists()
    if refresh_text:
        extracted_text = ""
    else:
        extracted_text = text_path.read_text(encoding="utf-8", errors="ignore")
        if is_image_type(record["filename"], content_type) and should_refresh_image_text(extracted_text):
            refresh_text = True

    if refresh_text:
        extracted_text = extract_text(file_path, content_type=content_type)
        text_path.write_text(extracted_text, encoding="utf-8")

    needs_chunks = refresh_text
    existing_chunks: list[dict] = []
    if chunks_path.exists() and not refresh_text:
        try:
            existing_chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
            needs_chunks = not bool(existing_chunks)
        except json.JSONDecodeError:
            needs_chunks = True

    if needs_chunks:
        chunks = build_chunks(file_path, extracted_text)
        chunks_path.write_text(json.dumps(chunks, ensure_ascii=True, indent=2), encoding="utf-8")
    else:
        chunks = existing_chunks

    record["content_type"] = detect_content_type(record["filename"], content_type)
    record["is_image"] = is_image_type(record["filename"], record["content_type"])
    record["has_text"] = bool(extracted_text.strip())
    record["char_count"] = len(extracted_text)
    record["chunk_count"] = len(chunks)
    return record


def sync_manifest_records() -> list[dict]:
    records = load_manifest()
    updated_records = [ensure_record_index(record) for record in records]
    save_manifest(updated_records)
    return updated_records


def normalize_terms(text: str) -> list[str]:
    return re.findall(r"[a-z0-9_]+", text.lower())


def extract_keywords(text: str) -> list[str]:
    terms = normalize_terms(text)
    keywords = [term for term in terms if term not in STOPWORDS and (len(term) > 2 or term.isdigit())]
    return keywords or terms


def best_fuzzy_match_score(term: str, candidates: set[str]) -> float:
    if len(term) < 4 or not candidates:
        return 0.0

    shortlisted = [
        candidate
        for candidate in candidates
        if candidate and abs(len(candidate) - len(term)) <= 3 and candidate[0] == term[0]
    ]
    if not shortlisted:
        return 0.0

    return max(difflib.SequenceMatcher(None, term, candidate).ratio() for candidate in shortlisted)


def score_chunk(question: str, chunk: str, filename: str = "") -> float:
    question_terms = extract_keywords(question)
    if not question_terms:
        return 0.0

    chunk_terms = normalize_terms(chunk)
    if not chunk_terms:
        return 0.0

    chunk_term_set = set(chunk_terms)
    filename_terms = set(normalize_terms(filename))
    searchable_terms = chunk_term_set | filename_terms

    score = 0.0
    matches = 0
    for term in question_terms:
        term_weight = 1.0 + min(len(term), 12) / 12
        if term in chunk_term_set:
            score += 4.0 * term_weight
            matches += 1
            continue
        if term in filename_terms:
            score += 3.0 * term_weight
            matches += 1
            continue

        fuzzy_score = best_fuzzy_match_score(term, searchable_terms)
        if fuzzy_score >= 0.84:
            score += 2.2 * fuzzy_score * term_weight
            matches += 1

    if matches == 0:
        return 0.0

    chunk_text_normalized = " ".join(chunk_terms)
    keyword_phrase = " ".join(question_terms)
    if keyword_phrase and keyword_phrase in chunk_text_normalized:
        score += 3.0

    if len(question_terms) >= 2:
        bigrams = [" ".join(question_terms[i : i + 2]) for i in range(len(question_terms) - 1)]
        score += 1.25 * sum(1 for bigram in bigrams if bigram in chunk_text_normalized)

    density = matches / max(len(chunk_term_set), 1)
    return round(score + density, 4)


def get_available_models() -> list[dict]:
    available: list[dict] = []
    seen: set[tuple[str, str]] = set()

    for option in MODEL_CATALOG:
        key_name = option.get("api_key_name")
        if key_name and not getattr(Config, key_name, None):
            continue

        key = (option["provider"], option["model_name"])
        if key in seen:
            continue
        seen.add(key)
        available.append(option)

    if available:
        return available

    return [
        {
            "model_id": "default",
            "label": "Default model",
            "provider": DEFAULT_PROVIDER,
            "model_name": DEFAULT_MODEL,
        }
    ]


def resolve_model_option(model_id: str | None = None) -> dict:
    models = get_available_models()
    model_map = {item["model_id"]: item for item in models}
    if model_id and model_id in model_map:
        return model_map[model_id]
    return model_map.get("default", models[0])


def select_records(
    file_ids: list[str] | None = None,
    search_all_files: bool = True,
) -> list[dict]:
    records = sync_manifest_records()
    if search_all_files:
        return records
    allowed = set(file_ids) #type: ignore
    return [record for record in records if record["file_id"] in allowed]


def retrieve_sources(
    question: str,
    file_ids: list[str] | None = None,
    search_all_files: bool = True,
    top_k: int = 4,
) -> list[SourceChunk]:
    sources: list[SourceChunk] = []
    seen_keys: set[tuple[str, int | None, str]] = set()
    for record in select_records(file_ids, search_all_files=search_all_files):
        chunks_path = CHUNKS_DIR / f"{record['file_id']}.json"
        if not chunks_path.exists():
            continue

        try:
            chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            chunks = []

        for index, chunk in enumerate(chunks, start=1):
            chunk_text = str(chunk.get("content", "")).strip()
            if not chunk_text:
                continue

            score = score_chunk(question, chunk_text, filename=record["filename"])
            if score <= 0:
                continue
            dedupe_key = (
                record["filename"].lower(),
                chunk.get("page_number"),
                chunk_text[:220],
            )
            if dedupe_key in seen_keys:
                continue
            seen_keys.add(dedupe_key)
            sources.append(
                SourceChunk(
                    file_id=record["file_id"],
                    filename=record["filename"],
                    chunk_index=index,
                    score=round(score, 4),
                    content=chunk_text[:1200],
                    is_image=bool(record.get("is_image")),
                    page_number=chunk.get("page_number"),
                )
            )

    return sorted(sources, key=lambda item: item.score, reverse=True)[:top_k]


def build_search_query(question: str, history: list[ChatTurn] | None = None) -> str:
    if not history:
        return question

    recent_history = [
        item.content.strip()
        for item in history[-6:]
        if item.role == "user" and item.content.strip()
    ]
    if not recent_history:
        return question
    return "\n".join(recent_history + [question])


def build_history_messages(history: list[ChatTurn] | None = None) -> list[HumanMessage | AIMessage]:
    messages: list[HumanMessage | AIMessage] = []
    if not history:
        return messages

    for item in history[-8:]:
        content = item.content.strip()
        if not content:
            continue
        if item.role == "user":
            messages.append(HumanMessage(content=content))
        elif item.role == "assistant":
            messages.append(AIMessage(content=content))
    return messages


@lru_cache(maxsize=16)
def get_llm(provider: str, model_name: str, temperature: float):
    factory = LLMFactory()
    return factory.get_llm(
        provider=provider,
        model_name=model_name,
        temperature=temperature,
    )


def build_context(sources: list[SourceChunk]) -> str:
    parts = []
    for source in sources:
        source_type = "image" if source.is_image else "document"
        parts.append(
            "\n".join(
                [
                    "<source>",
                    f"filename: {source.filename}",
                    f"type: {source_type}",
                    f"chunk: {source.chunk_index}",
                    f"page_number: {source.page_number or 'unknown'}",
                    f"content: {source.content}",
                    "</source>",
                ]
            )
        )
    return "\n\n".join(parts)


def answer_question(
    question: str,
    file_ids: list[str] | None = None,
    history: list[ChatTurn] | None = None,
    model_id: str | None = None,
    search_all_files: bool = True,
) -> AskResponse:
    search_query = build_search_query(question, history=history)
    sources = retrieve_sources(
        search_query,
        file_ids=file_ids,
        search_all_files=search_all_files,
    )
    if not sources:
        return AskResponse(
            answer="No matching content was found in the uploaded files.",
            sources=[],
            used_llm=False,
        )

    context = build_context(sources)

    try:
        model_option = resolve_model_option(model_id)
        llm = get_llm(
            model_option["provider"],
            model_option["model_name"],
            DEFAULT_TEMPERATURE,
        )
        messages: list[SystemMessage | HumanMessage | AIMessage] = [SystemMessage(content=SYSTEM_PROMPT)]
        messages.extend(build_history_messages(history))
        messages.append(
            HumanMessage(
                content=(
                    f"Question: {question}\n\n"
                    f"Context:\n{context}\n\n"
                    "Answer from the context only. Keep the main answer clean and do not add a Sources section."
                )
            )
        )
        response = llm.invoke(messages)
        answer = str(response.content) if hasattr(response, "content") else str(response)
        return AskResponse(answer=answer, sources=sources, used_llm=True)
    except Exception as exc:
        fallback = [
            "LLM response is unavailable right now.",
            f"Reason: {exc}",
            "",
            "Top matching context:",
        ]
        fallback.extend(
            f"- {source.filename} (chunk {source.chunk_index}): {source.content[:240]}"
            for source in sources
        )
        return AskResponse(answer="\n".join(fallback), sources=sources, used_llm=False)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/files")
def list_files() -> list[dict]:
    return sync_manifest_records()


@app.get("/models", response_model=ModelsResponse)
def list_models() -> ModelsResponse:
    models = [
        ModelOption(
            model_id=item["model_id"],
            label=item["label"],
            provider=item["provider"],
            model_name=item["model_name"],
        )
        for item in get_available_models()
    ]
    default_option = resolve_model_option(None)
    return ModelsResponse(default_model_id=default_option["model_id"], models=models)


@app.delete("/files/{file_id}")
def delete_file(file_id: str) -> dict:
    records = load_manifest()
    record = next((item for item in records if item["file_id"] == file_id), None)
    if record is None:
        raise HTTPException(status_code=404, detail="Uploaded file not found.")

    delete_record_files(record)
    updated_records = [item for item in records if item["file_id"] != file_id]
    save_manifest(updated_records)
    return {"status": "deleted", "file_id": file_id}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)) -> dict:
    filename = sanitize_filename(file.filename or "upload.bin")
    file_id = uuid.uuid4().hex
    target_path = UPLOAD_DIR / f"{file_id}_{filename}"

    content = await file.read()
    target_path.write_bytes(content)

    content_type = detect_content_type(filename, file.content_type)
    extracted_text = extract_text(target_path, content_type=content_type)
    text_path = TEXT_DIR / f"{file_id}.txt"
    text_path.write_text(extracted_text, encoding="utf-8")
    chunks = build_chunks(target_path, extracted_text)
    chunks_path = CHUNKS_DIR / f"{file_id}.json"
    chunks_path.write_text(json.dumps(chunks, ensure_ascii=True, indent=2), encoding="utf-8")

    record = {
        "file_id": file_id,
        "filename": filename,
        "path": str(target_path),
        "content_type": content_type,
        "is_image": is_image_type(filename, content_type),
        "size": len(content),
        "has_text": bool(extracted_text.strip()),
        "char_count": len(extracted_text),
        "chunk_count": len(chunks),
    }

    records = load_manifest()
    records.append(record)
    save_manifest(records)
    return record


@app.post("/ask", response_model=AskResponse)
def ask_question_route(payload: AskRequest) -> AskResponse:
    all_records = sync_manifest_records()
    if not all_records:
        raise HTTPException(status_code=400, detail="Upload at least one file first.")
    if not payload.search_all_files and not payload.file_ids:
        raise HTTPException(
            status_code=400,
            detail="Select at least one uploaded file or switch scope to all uploaded files.",
        )

    records = select_records(payload.file_ids, search_all_files=payload.search_all_files)
    if not records:
        raise HTTPException(status_code=404, detail="No matching uploaded files found.")

    return answer_question(
        payload.question,
        file_ids=payload.file_ids,
        history=payload.history,
        model_id=payload.model_id,
        search_all_files=payload.search_all_files,
    )


if __name__ == "__main__":
    uvicorn.run(app, host=API_HOST, port=API_PORT)
