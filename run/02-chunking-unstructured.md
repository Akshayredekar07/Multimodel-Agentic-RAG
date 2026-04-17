# Unstructured — Chunking Deep Dive

> Sources: Official Docs · Context7 · Unstructured readthedocs 0.12.6 · Unstructured Blog

---

## How Unstructured Chunking Differs from Normal Chunking

Most chunking libraries (LangChain, LlamaIndex) start from **raw text** and split on separators  
like `\n\n` or fixed token counts. Unstructured is fundamentally different:

Normal approach:     raw text → split by \n\n / tokens → chunks  
Unstructured:        raw doc  → partition() → Elements → chunk() → CompositeElements

Because `partition()` already understands document structure (Titles, Tables, ListItems, etc.),  
chunking only needs to **combine** or **split** elements — not blindly chop text.

> A single element is only text-split if it exceeds `max_characters`. Otherwise whole elements  
> are always preserved intact inside chunks.

---

## Output Element Types After Chunking

After any chunking strategy, you only get **3 element types**:

| Type | Description |
|------|-------------|
| `CompositeElement` | One or more combined text elements that fit within max size |
| `Table` | A Table element that fits within max size (never merged with others) |
| `TableChunk` | A Table that was too big and got text-split into parts |

---

## 4 Chunking Strategies — Availability Matrix

| Strategy | Open-Source Library | Serverless API / Platform |
|----------|:-------------------:|:-------------------------:|
| `basic` | | |
| `by_title` | | |
| `by_page` | | only |
| `by_similarity` | | only |

> `by_page` and `by_similarity` will **raise errors** if used with `partition_by_api=False`  
> in the open-source library. Only use them via the managed API/Platform.

---

## `basic` — Simple Sequential Packing

**Import:** `from unstructured.chunking.basic import chunk_elements`

### How it works
- Combines sequential elements greedily to fill up to `max_characters`
- When adding the next element would exceed the hard max → close chunk, start new
- A single oversized element is **isolated** (never combined) then **text-split**
- Tables are **always isolated** — never merged with other elements
- Overlap is applied only between text-split chunks (or all chunks if `overlap_all=True`)

### When to use
- Documents without clear section structure (emails, logs, raw text)
- When you just want max-filled chunks as fast as possible
- Simple RAG pipelines where semantic precision is less critical

---

## `by_title` — Section-Aware Semantic Chunking

**Import:** `from unstructured.chunking.title import chunk_by_title`

### How it works
- Everything from `basic` strategy, PLUS:
- **Title elements start a new chunk** — even if current chunk has room
- Ensures one chunk **never spans two sections**
- `multipage_sections=True` (default) — sections can cross pages  
- `multipage_sections=False` — page breaks also start a new chunk
- `combine_text_under_n_chars` — merges consecutive short sections to avoid tiny chunks

### When to use
- Structured docs: reports, contracts, research papers, manuals
- When retrieval precision matters (no cross-topic contamination in a chunk)
- RAG over financial, legal, or technical documentation

---

## `by_page` — Page-Boundary Chunking *(API only)*

### How it works
- Content from different pages is **never merged** into the same chunk
- When a new page is detected → current chunk closes → new chunk starts
- Even if next element would fit in current chunk

### When to use
- Documents where each page = a distinct unit (slides, forms, invoices)
- Financial/legal reports with page-level organization
- NVIDIA 2024 benchmarks: page-level chunking scored **0.648 accuracy** (best overall)

---

## `by_similarity` — Embedding-Based Topical Chunking *(API only)*

**Model used:** `sentence-transformers/multi-qa-mpnet-base-dot-v1`

### How it works
- Computes embeddings for each sequential element
- Groups elements with similarity **above** `similarity_threshold` (0.0–1.0)
- When similarity drops below threshold → close chunk → new chunk
- Still respects `max_characters` hard limit — even similar elements get split if too large
- Guarantees: two elements with similarity **below** threshold will **never** share a chunk

### When to use
- Documents without clear structure (news articles, transcripts, web scrapes)
- When topic shifts don't align with titles or page breaks
- Mixed-content documents where structure alone fails

---

## All Parameters Reference

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_characters` | int | 500 | **Hard max** — no chunk exceeds this. Oversized elements are text-split |
| `new_after_n_chars` | int | `max_characters` | **Soft max** — prefer to close chunk here, even if more would fit |
| `overlap` | int | 0 | Chars of overlap between chunks created by text-splitting |
| `overlap_all` | bool | False | Apply overlap between ALL chunks (not just text-split ones) use with caution |
| `combine_text_under_n_chars` | int | `max_characters` | (`by_title` only) Merge short consecutive sections. Set to 0 to disable |
| `multipage_sections` | bool | True | (`by_title` only) Allow sections to span page breaks |
| `include_orig_elements` | bool | True | Attach original source elements to `chunk.metadata.orig_elements` |
| `similarity_threshold` | float | — | (`by_similarity` only) Min similarity score (0.0–1.0) to merge elements |

### Parameter interaction: `max_characters` vs `new_after_n_chars`

max_characters=1500, new_after_n_chars=1000

Chunk fills elements until:  
→ hits 1000 chars (soft max) → stop adding even if next would fit under 1500  
→ hits 1500 chars (hard max) → text-split the oversized element

Use case: "I want ~1000 char chunks, but would rather have 1400 chars than cut mid-element"

---

## Key Behaviours to Know

- **Tables are sacred** — never combined with other elements. Always their own chunk.
- **Oversized element** — isolated first, then text-split. Split parts get `overlap` applied between them.
- **`overlap_all=True`** adds overlap between clean semantic chunk boundaries too — can "pollute" semantics, use carefully.
- **`combine_text_under_n_chars=0`** on `by_title` means every Title immediately starts a new chunk even if sections are tiny.
- **Inline chunking** — you can pass `chunking_strategy=` directly into `partition()` to chunk in one step.
- **Output type is always** `CompositeElement`, `Table`, or `TableChunk` — never original element types.

---

## RAG Performance Notes (Official Benchmarks)

From Unstructured's internal evaluation on FinanceBench (US SEC documents):

- Element-based chunking (`by_title`) outperformed fixed-token chunking in both retrieval accuracy and ROUGE/BLEU scores
- Smart chunking methods were more **generalizable** across novel document types
- Basic fixed-token strategies lacked consistency between page-level and paragraph-level accuracy
- Combining multiple chunking strategies yielded the best overall retrieval scores

From NVIDIA 2024 benchmarks (7 strategies, 5 datasets):

- `by_page` scored **0.648 accuracy** with lowest variance (0.107) — best for paginated docs
- Factoid queries: optimal at **256–512 tokens** per chunk
- Analytical queries: optimal at **1024+ tokens** per chunk

---

## References

| Source | URL |
|--------|-----|
| Official Chunking Docs | https://docs.unstructured.io/open-source/core-functionality/chunking |
| Chunking Strategies (API) | https://docs.unstructured.io/api-reference/api-services/chunking |
| Readthedocs 0.12.6 | https://unstructured.readthedocs.io/en/latest/core/chunking.html |
| RAG Performance Blog | https://unstructured.io/blog/unstructured-s-preprocessing-pipelines-enable-enhanced-rag-performance |
| RAG Best Practices Blog | https://unstructured.io/blog/chunking-for-rag-best-practices |



