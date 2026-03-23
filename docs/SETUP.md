# Setup Guide

This project uses `unstructured.partition.pdf` with `strategy="hi_res"`, which requires the Tesseract OCR system binary (`tesseract.exe`/`tesseract`).

`HF_TOKEN` is separate and does not replace Tesseract.

## Windows (PowerShell)

### 1. Install Tesseract OCR

1. Open: https://github.com/UB-Mannheim/tesseract/wiki
2. Download the latest Windows installer.
3. Run the installer with default path:
   - `C:\Program Files\Tesseract-OCR`
4. Ensure English language data is selected (and any other needed languages).

### 2. Verify binary exists

```powershell
& "C:\Program Files\Tesseract-OCR\tesseract.exe" --version
```

If this command fails, installation path is wrong or installation did not complete.

### 3. Add to PATH (User scope)

```powershell
[Environment]::SetEnvironmentVariable(
  "Path",
  $env:Path + ";C:\Program Files\Tesseract-OCR",
  "User"
)
```

Close and reopen terminal/VS Code/Jupyter after updating PATH.

### 4. Verify PATH resolution

```powershell
tesseract --version
```

### 5. Notebook-safe explicit config (recommended)

Add this before `partition_pdf(...)`:

```python
import os
from unstructured_pytesseract import pytesseract

pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR\tessdata"  # optional
```

## Linux

### Ubuntu/Debian

```bash
sudo apt update
sudo apt install -y tesseract-ocr tesseract-ocr-eng
```

Optional additional languages (example):

```bash
sudo apt install -y tesseract-ocr-hin
```

### Fedora

```bash
sudo dnf install -y tesseract tesseract-langpack-eng
```

### Arch

```bash
sudo pacman -S --needed tesseract tesseract-data-eng
```

### Verify install

```bash
tesseract --version
```

### Optional explicit config in Python

Usually not required if PATH is set, but can be forced:

```python
from unstructured_pytesseract import pytesseract
pytesseract.tesseract_cmd = "/usr/bin/tesseract"
```

## Quick Troubleshooting

- `TesseractNotFoundError`: Python wrapper installed, system binary missing/not on PATH.
- Restart Jupyter kernel after install or PATH changes.
- Confirm path from Python:

```python
import os
print(os.path.exists(r"C:\Program Files\Tesseract-OCR\tesseract.exe"))
```

## Minimal test snippet

```python
from unstructured.partition.pdf import partition_pdf
import os
from unstructured_pytesseract import pytesseract

# Windows example path (adjust if needed)
pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
os.makedirs("./extracted_images", exist_ok=True)

elements = partition_pdf(
    filename="attention.pdf",
    strategy="hi_res",
    extract_image_block_types=["Image", "Table"],
    extract_image_block_output_dir="./extracted_images",
    extract_image_block_to_payload=False,
    infer_table_structure=True,
    hi_res_model_name="yolox",
)
```
