# Getting Started with Unstructured (Open-Source)

> **Unstructured** is an open-source Python library that converts raw, messy documents  
> (PDFs, Word files, HTML, images, emails, etc.) into clean, structured JSON/text formats  
> ready for LLMs, RAG pipelines, and vector databases.

---

## Installation

### Minimal install (plain text files only)
```bash
pip install unstructured
```

### Full install (all document types — recommended)
```bash
pip install "unstructured[all-docs]"
```

### Install for specific file types
```bash
pip install "unstructured[pdf]"        # PDFs only
pip install "unstructured[docx]"       # Word documents only
pip install "unstructured[image]"      # Images only
pip install "unstructured[pptx]"       # PowerPoint only
pip install "unstructured[xlsx]"       # Excel only
pip install "unstructured[md]"         # Markdown only
pip install "unstructured[html]"       # HTML only
pip install "unstructured[msg]"        # Email (.msg) only
```

### System dependencies (for PDF/image support)
```bash
# Ubuntu/Debian
sudo apt-get install -y poppler-utils tesseract-ocr libmagic1

# macOS
brew install poppler tesseract libmagic
```

---

## Supported File Types (60+)

| Category      | Formats                                      |
|---------------|----------------------------------------------|
| Documents     | PDF, DOCX, DOC, ODT, RTF                     |
| Presentations | PPTX, PPT                                    |
| Spreadsheets  | XLSX, XLS, CSV, TSV                          |
| Web           | HTML, XML, RST, ORG                          |
| Emails        | EML, MSG                                     |
| Images        | PNG, JPG, TIFF, BMP, HEIC                   |
| eBooks        | EPUB                                         |
| Text          | TXT, MD, LOG                                 |
| Code          | PY, JS, TS, JAVA, C, CPP, GO, YAML, TOML   |

---

## Core Concepts

| Concept        | Description |
|----------------|-------------|
| **Partition**  | Split a document into typed elements (Title, NarrativeText, Table, Image, etc.) |
| **Element**    | A single piece of content with metadata (page, coordinates, file info) |
| **Chunk**      | Group elements into passages of a target size for vector DB ingestion |
| **Stage**      | Format/convert elements for a specific destination (CSV, dict, JSON) |
| **Clean**      | Normalize text — remove boilerplate, fix encoding, clean whitespace |

---

## Quickstart

### 1. Auto-detect and partition any file
```python
from unstructured.partition.auto import partition

# Works on PDF, DOCX, HTML, images — auto-detects format
elements = partition(filename="your_document.pdf")

for el in elements:
    print(type(el).__name__, "→", el.text[:80])
```

**Output:**
```
Title → Introduction to Machine Learning
NarrativeText → Machine learning is a branch of AI that enables systems...
Table → | Feature | Value | Score |
Image → [Image with caption: Figure 1. Neural network architecture]
```

---

## Document Partitioning — By File Type

### PDF Partitioning
```python
from unstructured.partition.pdf import partition_pdf

# Basic partition
elements = partition_pdf(filename="report.pdf")

# With OCR for scanned PDFs (requires tesseract)
elements = partition_pdf(
    filename="scanned_report.pdf",
    strategy="ocr_only",           # force OCR
    languages=["eng"],             # OCR language
)

# Hi-res mode: extracts tables + images via layout model
elements = partition_pdf(
    filename="complex_report.pdf",
    strategy="hi_res",             # best quality, slower
    infer_table_structure=True,    # extract table HTML
    extract_images_in_pdf=True,    # save images to disk
    extract_image_block_output_dir="./extracted_images/",
)

# Fast mode for digital PDFs (no OCR)
elements = partition_pdf(
    filename="digital.pdf",
    strategy="fast",               # fastest, text-only
)

print(f"Total elements: {len(elements)}")
for el in elements[:5]:
    print(f"[{type(el).__name__}] {el.text[:100]}")
```

---

### Word Document (DOCX) Partitioning
```python
from unstructured.partition.docx import partition_docx

elements = partition_docx(filename="contract.docx")

# Inspect element types
from collections import Counter
type_counts = Counter(type(el).__name__ for el in elements)
print("Element type distribution:", type_counts)
# → Counter({'NarrativeText': 45, 'Title': 12, 'ListItem': 8, 'Table': 3})

# Filter only titles
titles = [el for el in elements if type(el).__name__ == "Title"]
for t in titles:
    print(" ", t.text)
```

---

### HTML Partitioning
```python
from unstructured.partition.html import partition_html

# From local file
elements = partition_html(filename="webpage.html")

# From URL (live web page)
elements = partition_html(url="https://en.wikipedia.org/wiki/Artificial_intelligence")

for el in elements[:10]:
    print(f"[{type(el).__name__}] {el.text[:100]}")
```

---

### Image Partitioning (with OCR)
```python
from unstructured.partition.image import partition_image

# Extract text from image (requires tesseract)
elements = partition_image(
    filename="screenshot.png",
    strategy="hi_res",       # use layout model
    languages=["eng"],
)

for el in elements:
    print(el.text)
```

---

### Email (.eml) Partitioning
```python
from unstructured.partition.email import partition_email

elements = partition_email(filename="newsletter.eml")

# Emails have special metadata
for el in elements:
    print(f"[{type(el).__name__}] {el.text[:80]}")
    if hasattr(el.metadata, 'sent_from'):
        print("  From:", el.metadata.sent_from)
```

---

### Excel / CSV Partitioning
```python
from unstructured.partition.xlsx import partition_xlsx
from unstructured.partition.csv import partition_csv

# Excel
elements = partition_xlsx(filename="data.xlsx")

# CSV
elements = partition_csv(filename="data.csv")

# Tables are returned as Table elements with HTML representation
for el in elements:
    if type(el).__name__ == "Table":
        print("Table HTML:", el.metadata.text_as_html[:200])
```

---

### PowerPoint Partitioning
```python
from unstructured.partition.pptx import partition_pptx

elements = partition_pptx(filename="slides.pptx")

for el in elements:
    print(f"[Slide {el.metadata.page_number}] [{type(el).__name__}] {el.text[:80]}")
```

---

## Working with Elements & Metadata

```python
from unstructured.partition.pdf import partition_pdf

elements = partition_pdf(filename="report.pdf")

# Each element has rich metadata
el = elements[0]
print("Text:       ", el.text)
print("Type:       ", type(el).__name__)
print("Page:       ", el.metadata.page_number)
print("Filename:   ", el.metadata.filename)
print("File type:  ", el.metadata.filetype)
print("Coordinates:", el.metadata.coordinates)   # bounding box

# Convert single element to dict
print(el.to_dict())
```

**Element Types Reference:**

| Type              | Meaning                                      |
|-------------------|----------------------------------------------|
| `Title`           | Section/document heading                     |
| `NarrativeText`   | Body paragraphs                              |
| `ListItem`        | Bullet or numbered list item                 |
| `Table`           | Table (with HTML in metadata)                |
| `Image`           | Embedded image                               |
| `Header`          | Page header                                  |
| `Footer`          | Page footer                                  |
| `FigureCaption`   | Caption under a figure                       |
| `Address`         | Postal address                               |
| `EmailAddress`    | Email address                                |
| `CodeSnippet`     | Code block                                   |
| `PageBreak`       | Page separator                               |

---

## Chunking Elements

Chunking groups elements into passages of a target token/character size — perfect for vector DB ingestion.

```python
from unstructured.partition.pdf import partition_pdf
from unstructured.chunking.title import chunk_by_title
from unstructured.chunking.basic import chunk_elements

elements = partition_pdf(filename="long_report.pdf")

# --- Method 1: Chunk by Title (respects section boundaries) ---
chunks = chunk_by_title(
    elements,
    max_characters=1000,       # max chunk size in characters
    new_after_n_chars=800,     # soft limit — start new chunk after this
    combine_text_under_n_chars=200,  # combine short sections
    overlap=50,                # character overlap between chunks
)

for i, chunk in enumerate(chunks):
    print(f"\n--- Chunk {i+1} ---")
    print(f"Characters: {len(chunk.text)}")
    print(chunk.text[:200])

# --- Method 2: Basic chunking (fixed-size) ---
chunks = chunk_elements(
    elements,
    max_characters=500,
    overlap=50,
)

print(f"\nTotal chunks: {len(chunks)}")
```

---

## Text Cleaning

```python
from unstructured.cleaners.core import (
    clean,
    clean_non_ascii_chars,
    clean_extra_whitespace,
    clean_dashes,
    clean_bullets,
    replace_unicode_quotes,
    group_broken_paragraphs,
)

raw_text = "  Hello,   world!!  \n\n  This is  broken\ntext.  "

# Clean extra whitespace
cleaned = clean_extra_whitespace(raw_text)
print(cleaned)  # "Hello, world!! This is broken text."

# Full pipeline clean
cleaned = clean(
    raw_text,
    extra_whitespace=True,
    dashes=True,
    bullets=True,
    trailing_punctuation=False,
    lowercase=False,
)
print(cleaned)

# Fix unicode quotes
text = "\u201cHello\u201d he said"
print(replace_unicode_quotes(text))   # "Hello" he said

# Remove non-ASCII characters
text = "Héllo wörld"
print(clean_non_ascii_chars(text))   # Hllo wrld

# Fix broken paragraphs (PDF extraction artifacts)
broken = "This is a sentence that got\nbroken across lines\ninappropriately."
fixed = group_broken_paragraphs(broken)
print(fixed)  # "This is a sentence that got broken across lines inappropriately."
```

---

## Staging — Exporting to Different Formats

```python
from unstructured.partition.pdf import partition_pdf
from unstructured.staging.base import (
    elements_to_json,
    elements_from_json,
    convert_to_dict,
    elements_to_text,
)

elements = partition_pdf(filename="report.pdf")

# --- Export to JSON ---
json_str = elements_to_json(elements)
print(json_str[:300])

# Save JSON to file
elements_to_json(elements, filename="output.json")

# Load back from JSON
elements_reloaded = elements_from_json(filename="output.json")

# --- Export to plain text ---
text = elements_to_text(elements)
print(text[:500])

# --- Export to list of dicts ---
dicts = convert_to_dict(elements)
for d in dicts[:2]:
    print(d)
# → {'type': 'Title', 'text': 'Introduction', 'metadata': {...}}
```

---

## Full RAG Pipeline Example

This example shows a complete pipeline: PDF → partition → chunk → embed → vector store.

```python
import json
from unstructured.partition.pdf import partition_pdf
from unstructured.chunking.title import chunk_by_title
from unstructured.staging.base import elements_to_json
from unstructured.cleaners.core import clean_extra_whitespace

# ─────────────────────────────────────────────
# Step 1: Partition the document
# ─────────────────────────────────────────────
print("Partitioning document...")
elements = partition_pdf(
    filename="research_paper.pdf",
    strategy="hi_res",
    infer_table_structure=True,
)
print(f"   Found {len(elements)} elements")

# ─────────────────────────────────────────────
# Step 2: Clean text in each element
# ─────────────────────────────────────────────
print("Cleaning text...")
for el in elements:
    if el.text:
        el.text = clean_extra_whitespace(el.text)

# ─────────────────────────────────────────────
# Step 3: Chunk into passages
# ─────────────────────────────────────────────
print(" Chunking...")
chunks = chunk_by_title(
    elements,
    max_characters=1200,
    new_after_n_chars=1000,
    overlap=100,
)
print(f"   Created {len(chunks)} chunks")

# ─────────────────────────────────────────────
# Step 4: Prepare for vector DB
# ─────────────────────────────────────────────
documents = []
for i, chunk in enumerate(chunks):
    documents.append({
        "id": f"chunk_{i}",
        "text": chunk.text,
        "metadata": {
            "source": chunk.metadata.filename,
            "page": chunk.metadata.page_number,
            "type": type(chunk).__name__,
        }
    })

print("\n Sample document ready for vector DB:")
print(json.dumps(documents[0], indent=2))

# ─────────────────────────────────────────────
# Step 5: Save intermediate output
# ─────────────────────────────────────────────
elements_to_json(elements, filename="partitioned.json")
print("\n Saved partitioned.json")
```

---

##  Docker Usage

```bash
# Pull the official container
docker pull downloads.unstructured.io/unstructured-io/unstructured:latest

# Run on a file
docker run -v $(pwd):/files \
  downloads.unstructured.io/unstructured-io/unstructured:latest \
  python -c "
from unstructured.partition.auto import partition
els = partition('/files/document.pdf')
for e in els: print(e.text[:80])
"
```

---

## Configuration Tips

```python
# Check available strategies
from unstructured.partition.pdf import partition_pdf

# strategy options:
# "fast"    → text-only, fastest (digital PDFs)
# "hi_res"  → layout detection, best quality (needs detectron2)
# "ocr_only"→ force OCR on every page (scanned docs)
# "auto"    → default, smart selection

# Specify OCR languages (ISO 639-2)
elements = partition_pdf(
    filename="french_doc.pdf",
    strategy="ocr_only",
    languages=["fra"],   # French
)

# Enable verbose logging
import logging
logging.getLogger("unstructured").setLevel(logging.DEBUG)
```

---

## Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| `ImportError: cannot import name 'partition_pdf'` | `pip install "unstructured[pdf]"` |
| `TesseractNotFound` | Install tesseract: `sudo apt install tesseract-ocr` |
| `PdfminerException` | Install poppler: `sudo apt install poppler-utils` |
| Garbled text from scanned PDF | Use `strategy="ocr_only"` |
| Tables not extracted properly | Use `strategy="hi_res"` with `infer_table_structure=True` |
| Slow performance on large files | Use `strategy="fast"` for digital PDFs |

---

## 🔗 Resources

| Resource | Link |
|----------|-------|
| GitHub | https://github.com/Unstructured-IO/unstructured |
| Docs | https://docs.unstructured.io |
| PyPI | https://pypi.org/project/unstructured |
| Discord | https://discord.gg/unstructured |
| Examples | https://github.com/Unstructured-IO/unstructured/tree/main/examples |

---

> **Tip:** For production RAG systems, combine the open-source library for local dev/testing  
> with the **Unstructured Platform API** for scalable, managed cloud processing.


There are **17 specific partition functions** plus 1 universal one. Here is the complete list with correct imports and usage:


**The universal one — use this when you don't want to think about file type**

```python
from unstructured.partition.auto import partition

elements = partition(filename="any_file.pdf")   # auto-detects format
```


**All 17 file-specific partition functions**

```python
# 1. PDF
from unstructured.partition.pdf import partition_pdf
elements = partition_pdf(filename="doc.pdf", strategy="hi_res")

# 2. Word Document
from unstructured.partition.docx import partition_docx
elements = partition_docx(filename="doc.docx")

# 3. Legacy Word (.doc — older format)
from unstructured.partition.doc import partition_doc
elements = partition_doc(filename="doc.doc")

# 4. PowerPoint
from unstructured.partition.pptx import partition_pptx
elements = partition_pptx(filename="slides.pptx")

# 5. Legacy PowerPoint (.ppt)
from unstructured.partition.ppt import partition_ppt
elements = partition_ppt(filename="slides.ppt")

# 6. Excel
from unstructured.partition.xlsx import partition_xlsx
elements = partition_xlsx(filename="data.xlsx", include_header=True)

# 7. CSV
from unstructured.partition.csv import partition_csv
elements = partition_csv(filename="data.csv", delimiter=",")

# 8. TSV
from unstructured.partition.tsv import partition_tsv
elements = partition_tsv(filename="data.tsv")

# 9. HTML
from unstructured.partition.html import partition_html
elements = partition_html(filename="page.html")
elements = partition_html(url="https://example.com/article")   # also accepts URL

# 10. Plain Text
from unstructured.partition.text import partition_text
elements = partition_text(filename="notes.txt")
elements = partition_text(text="raw string content here")      # also accepts raw string

# 11. Markdown
from unstructured.partition.md import partition_md
elements = partition_md(filename="README.md")

# 12. RST (ReStructuredText — Python docs format)
from unstructured.partition.rst import partition_rst
elements = partition_rst(filename="docs.rst")

# 13. ORG (Emacs org-mode)
from unstructured.partition.org import partition_org
elements = partition_org(filename="notes.org")

# 14. XML
from unstructured.partition.xml import partition_xml
elements = partition_xml(filename="data.xml", xml_keep_tags=False)

# 15. Image (PNG, JPG, TIFF, BMP, HEIC)
from unstructured.partition.image import partition_image
elements = partition_image(filename="scan.png", strategy="hi_res", languages=["eng"])

# 16. Email — .eml format
from unstructured.partition.email import partition_email
elements = partition_email(filename="message.eml", process_attachments=True)

# 17. Email — .msg format (Outlook)
from unstructured.partition.msg import partition_msg
elements = partition_msg(filename="message.msg", process_attachments=True)

# 18. EPUB (eBook)
from unstructured.partition.epub import partition_epub
elements = partition_epub(filename="book.epub")
```


**Quick reference table**

| Function | File Type | Accepts URL | OCR support | strategy param |
|---|---|:---:|:---:|:---:|
| `partition_pdf` | .pdf | No | Yes | Yes |
| `partition_docx` | .docx | No | No | No |
| `partition_doc` | .doc | No | No | No |
| `partition_pptx` | .pptx | No | No | No |
| `partition_ppt` | .ppt | No | No | No |
| `partition_xlsx` | .xlsx | No | No | No |
| `partition_csv` | .csv | No | No | No |
| `partition_tsv` | .tsv | No | No | No |
| `partition_html` | .html | Yes | No | No |
| `partition_text` | .txt | No | No | No |
| `partition_md` | .md | No | No | No |
| `partition_rst` | .rst | No | No | No |
| `partition_org` | .org | No | No | No |
| `partition_xml` | .xml | No | No | No |
| `partition_image` | .png .jpg .tiff | No | Yes | Yes |
| `partition_email` | .eml | No | No | No |
| `partition_msg` | .msg | No | No | No |
| `partition_epub` | .epub | No | No | No |


**Rule of thumb:** `strategy="hi_res"` and OCR are only available on `partition_pdf` and `partition_image` because those are the only two types where content may be non-digital (scanned/rendered). Everything else is structured markup so layout models are not needed.