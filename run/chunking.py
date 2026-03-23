import base64
from pathlib import Path
from unstructured.partition.pdf import partition_pdf
from unstructured.chunking.title import chunk_by_title
from unstructured.documents.elements import Image, Table, FigureCaption, CompositeElement


def partition_document(filepath: str) -> list:
    return partition_pdf(
        filename=filepath,
        strategy="hi_res",
        infer_table_structure=True,
        extract_image_block_types=["Image", "Table"],
        extract_image_block_to_payload=True,
    )


def process_images(raw_chunks: list, vision_llm) -> list:
    from langchain_core.messages import HumanMessage

    processed = []

    for idx, chunk in enumerate(raw_chunks):
        if not isinstance(chunk, Image):
            continue

        caption = (
            raw_chunks[idx + 1].text
            if idx + 1 < len(raw_chunks) and isinstance(raw_chunks[idx + 1], FigureCaption)
            else "No caption available"
        )

        b64 = chunk.metadata.image_base64
        image_text = chunk.text or ""
        description = image_text  # fallback

        if b64:
            try:
                response = vision_llm.invoke([
                    HumanMessage(content=[
                        {"type": "text", "text": (
                            f"Describe this figure from a research paper.\n"
                            f"Caption: {caption}\n"
                            f"OCR text: {image_text or 'none'}\n"
                            f"Provide a 2-3 sentence technical description."
                        )},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                    ])
                ])
                description = response.content
            except Exception as e:
                print(f"Vision LLM error on image #{idx}: {e}")

        processed.append({
            "content"      : description,
            "content_type" : "image",
            "caption"      : caption,
            "image_text"   : image_text,
            "base64_image" : b64,
            "page"         : chunk.metadata.page_number,
            "filename"     : chunk.metadata.filename,
        })

    print(f"Processed {len(processed)} images")
    return processed


def process_tables(raw_chunks: list, text_llm) -> list:
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser

    processed = []
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a technical document analyst. Summarize the following HTML table in 2-3 sentences. Be direct, no preamble."),
        ("human", "{table_html}"),
    ])
    chain = prompt | text_llm | StrOutputParser()

    for chunk in raw_chunks:
        if not isinstance(chunk, Table):
            continue

        description = chunk.text  # fallback
        try:
            description = chain.invoke({"table_html": chunk.metadata.text_as_html or chunk.text})
        except Exception as e:
            print(f"Table LLM error: {e}")

        processed.append({
            "content"      : description,
            "content_type" : "table",
            "table_html"   : chunk.metadata.text_as_html,
            "table_text"   : chunk.text,
            "page"         : chunk.metadata.page_number,
            "filename"     : chunk.metadata.filename,
        })

    print(f"Processed {len(processed)} tables")
    return processed


def process_text_chunks(raw_chunks: list) -> list:
    chunks = chunk_by_title(
        raw_chunks,
        max_characters=2000,
        new_after_n_chars=1500,
        combine_text_under_n_chars=500,
        include_orig_elements=False,
    )

    processed = [
        {
            "content"      : chunk.text,
            "content_type" : "text",
            "page"         : chunk.metadata.page_number,
            "filename"     : chunk.metadata.filename,
        }
        for chunk in chunks
        if isinstance(chunk, CompositeElement) and chunk.text.strip()
    ]

    print(f"Processed {len(processed)} text chunks")
    return processed