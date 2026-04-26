# Tesseract OCR Setup for EvidenceVault

EvidenceVault requires Tesseract OCR to extract text from uploaded screenshots. Follow the steps below:

## Windows Installation

### Option 1: Using Chocolatey (Recommended)
```powershell
choco install tesseract
```

### Option 2: Manual Installation
1. Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer (e.g., `tesseract-ocr-w64-setup-v5.x.x.exe`)
3. During installation, note the installation path (usually `C:\Program Files\Tesseract-OCR`)

### Option 3: Using Windows Store (Windows 10+)
```powershell
winget install UB-Mannheim.TesseractOCR
```

---

## Verify Installation

Run this command in PowerShell to verify:
```powershell
tesseract --version
```

Expected output:
```
tesseract 5.x.x
  ...
```

---

## If Tesseract is Not Found in PATH

If you installed Tesseract but it's not in your system PATH, set it explicitly:

### Windows PowerShell
```powershell
$env:TESSERACT_CMD = "C:\Program Files\Tesseract-OCR\tesseract.exe"
python app.py
```

### Or Add to Environment Variables Permanently
1. Press `Win + X` → Search "Environment Variables"
2. Click "Edit the system environment variables"
3. Click "Environment Variables" → "New" (under System variables)
4. Variable name: `TESSERACT_CMD`
5. Variable value: `C:\Program Files\Tesseract-OCR\tesseract.exe`
6. Click OK, restart PowerShell

---

## Test OCR Extraction

1. Start the app: `python app.py`
2. Go to http://127.0.0.1:5000
3. Upload a screenshot with readable text
4. Check terminal for: `[Tesseract OCR] ✓ Extracted XXX chars`

---

## Troubleshooting

### "tesseract is not installed or it's not in your PATH"
- Run: `tesseract --version` to check if installed
- If not found, install using Chocolatey (Option 1 above)
- Or set `TESSERACT_CMD` environment variable

### "Unsupported image format"
- Try PNG or JPEG formats
- Avoid BMP, WebP, or other formats

### "No text detected"
- Image might be too dark/light/blurry
- Try taking a clearer screenshot
- Text should have high contrast

---

## Gemini Model Fallback

If Gemini API keys fail, the app will automatically fall back to Tesseract OCR.

Models tried (in order):
1. `gemini-1.5-flash` (latest)
2. `gemini-pro-vision` (vision-capable)
3. `gemini-pro` (fallback)
4. **Tesseract OCR** (local, no API needed)

---

## Questions?

- EvidenceVault: http://127.0.0.1:5000
- Tesseract docs: https://github.com/UB-Mannheim/tesseract/wiki
