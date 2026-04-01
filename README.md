### Multimodal RAG Workspace

This project combines a FastAPI backend with a Streamlit chat UI for document question answering. You can upload files, extract text, chunk content, retrieve relevant passages, and generate grounded answers with a selectable LLM provider.

### Demo Video

[Watch the demo video](docs/demo-vid.mp4)

### What It Does

- Upload and manage documents from the Streamlit interface.
- Ask questions across all files or limit search to selected files.
- Extract text from PDFs, DOCX files, markdown, plain text, CSV, JSON, and images.
- Use OCR for images and optionally generate image summaries when a vision-capable model is available.
- Switch between supported LLM providers based on the API keys present in your `.env`.

### Supported Inputs And Runtime Flow

- Supported upload types in the UI: `pdf`, `txt`, `md`, `docx`, `doc`, `png`, `jpg`, `jpeg`, `webp`, `csv`, and `json`.
- Uploaded files are stored in `uploaded_files/`.
- Extracted text is saved in `uploaded_files/extracted_text/`.
- Retrieval chunks are saved in `uploaded_files/chunks/`.
- The backend ranks chunks with keyword and fuzzy matching, then sends the best context to the selected model for the final answer.

### Setup

1. Create and activate a virtual environment.
2. Install the dependencies.
3. Copy `.env.example` to `.env`.
4. Add at least one model provider API key.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

If you want OCR for images, install Tesseract on your machine and make sure it is available in your system `PATH`.

### Environment Variables

Minimum setup:

```env
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GOOGLE_API_KEY=
GROQ_API_KEY=
NVIDIA_API_KEY=
CEREBRAS_API_KEY=
NEBIUS_API_KEY=
OPENROUTER_API_KEY=
HUGGINGFACEHUB_API_TOKEN=
```

Optional runtime settings used by the app:

```env
API_HOST=127.0.0.1
API_PORT=8000
API_BASE_URL=http://127.0.0.1:8000
MAIN_LLM_PROVIDER=nebius
MAIN_LLM_MODEL=MiniMaxAI/MiniMax-M2.5
MAIN_LLM_LABEL=MiniMax-M2.5
MAIN_LLM_TEMPERATURE=0.2
ENABLE_IMAGE_SUMMARY=false
ENABLE_UNSTRUCTURED_IMAGE_OCR=false
```

### Run The App

Start the FastAPI backend in one terminal:

```powershell
python main.py
```

Start the Streamlit UI in another terminal:

```powershell
streamlit run streamlit_app.py
```

Open the Streamlit URL shown in the terminal, upload files, and begin chatting with your documents.

### Docker

You can also run the backend and Streamlit UI in one container with the included `Dockerfile`.

```dockerfile
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    API_HOST=0.0.0.0 \
    API_PORT=8000 \
    API_BASE_URL=http://127.0.0.1:8000 \
    STREAMLIT_SERVER_PORT=8501

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    libglib2.0-0 \
    libgl1 \
    libmagic1 \
    tesseract-ocr \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

RUN mkdir -p uploaded_files/extracted_text uploaded_files/chunks data
RUN chmod +x docker-entrypoint.sh

EXPOSE 8000 8501

CMD ["./docker-entrypoint.sh"]
```

```bash
docker build -t multimodal-rag .
docker run --env-file .env -p 8000:8000 -p 8501:8501 multimodal-rag
```

After the container starts, open `http://localhost:8501`.

### Project Layout

- `main.py`: FastAPI app for upload, retrieval, model listing, and question answering.
- `streamlit_app.py`: Streamlit interface for chats, file management, and model selection.
- `config.py`: environment-based configuration and provider key lookup.
- `src/model_providers.py`: provider factory for OpenAI, Anthropic, Gemini, Groq, Ollama, Nvidia, Cerebras, Nebius, OpenRouter, Hugging Face, and vLLM.
- `src/ingestion/chunkers.py`: chunking logic with unstructured-based and fallback chunking paths.
- `uploaded_files/`: stored uploads, extracted text, chunk files, and the upload manifest.
