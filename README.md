# magazineTranslator

## 📖 Overview

**magazineTranslator** is a personal project created to make reading Japanese magazines easier.  
It automatically extracts text from magazine images using OCR (Optical Character Recognition) and translates Japanese text into Korean using Azure Translator.  
The entire process is asynchronous, improving speed and efficiency, and outputs neatly structured JSON files.

Other versions: [한국어](./README_kr.md)
---

## 🚀 Features

- **Automatic ZIP Extraction**  
  Automatically extracts image files from ZIP archives placed inside the `01_input_zips` folder.

- **OCR Processing (EasyOCR)**  
  Uses the EasyOCR model (`ja`, `en`) to recognize text and merge detected lines into coherent paragraphs.

- **Asynchronous Translation (Azure Translator)**  
  Translates extracted text into Korean using the Azure Translator API.  
  API keys and settings are stored securely in a `.env` file.

- **Organized Output**  
  Stores translation results as JSON files in the `03_output_results` folder, one per magazine.

- **Automatic Cleanup**  
  Temporary images in `02_temp_images` are deleted after translation completes.

---

## 🧩 Directory Structure

```
magazinetranslator/
│
├── main.py                # Main orchestrator for OCR and translation pipeline
├── ocr_processor.py       # EasyOCR-based text extraction and paragraph merging
├── api_clients.py         # Azure Translator API client
├── check_apis.py          # API key validation script
├── test_paddle_load.py    # PaddleOCR GPU environment check
│
├── 01_input_zips/         # Input ZIP files directory
├── 02_temp_images/        # Temporary images extracted from ZIPs
└── 03_output_results/     # Final translated JSON output files
```

---

## ⚙️ Installation & Setup

### 1. Install Required Packages

```bash
pip install easyocr httpx python-dotenv torch opencv-python Pillow numpy
```

(Optionally, for GPU support: `paddlepaddle-gpu`, `paddleocr`)

### 2. Configure Environment Variables

Create a `.env` file in the project root with the following keys:

```env
AZURE_TRANSLATOR_KEY=your_azure_key
AZURE_TRANSLATOR_ENDPOINT=https://api.cognitive.microsofttranslator.com
AZURE_TRANSLATOR_REGION=koreacentral
```

(Optional) For Gemini API testing:

```env
GEMINI_API_KEY=your_gemini_key
```

---

## 🖥️ Usage

1. Place the ZIP files containing magazine images in `01_input_zips/`.  
   (e.g., `weekly_magazine_2025_01.zip`)

2. Run the script:
   ```bash
   python main.py
   ```

3. When finished, check the `03_output_results/` folder for translated JSON files.

---

## 🧾 Example Output (JSON)

```json
{
  "magazine_name": "weekly_magazine_2025_01",
  "total_pages": 3,
  "pages": [
    {
      "page_number": 1,
      "original_filename": "001.png",
      "blocks": [
        {
          "box": [30, 40, 150, 25],
          "original_text": "新しい生活",
          "translated_text": "New Life"
        }
      ]
    }
  ]
}
```

---

## 💡 Notes

- EasyOCR and Azure Translator run asynchronously for better performance.  
- Logs and progress updates are printed to the console during execution.  
- The OCR engine automatically detects GPU availability and falls back to CPU if needed.

---

## 🧑‍💻 Author

**Developer:** Hyunmyung (Steve) Park  
**Purpose:** A personal automation tool for translating Japanese magazines efficiently.
