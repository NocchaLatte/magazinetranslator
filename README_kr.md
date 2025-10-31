# magazineTranslator

## 📖 개요

**magazineTranslator**는 일본어로 된 잡지를 쉽게 읽기 위해 개발된 프로젝트입니다.  
이미지 기반 잡지를 OCR(광학 문자 인식)으로 분석하여 텍스트를 추출하고, 추출된 일본어 텍스트를 한국어로 번역합니다.  
비동기 파이프라인을 통해 여러 페이지를 동시에 처리하며, 결과를 JSON 파일로 정리합니다.

---

## 🚀 주요 기능

- **ZIP 압축 해제 자동화**  
  `01_input_zips` 폴더 내 ZIP 파일을 자동으로 해제하고 이미지 파일을 추출합니다.

- **OCR 처리 (EasyOCR)**  
  EasyOCR 모델(`ja`, `en`)을 사용하여 텍스트 블록을 감지하고 문단 단위로 병합합니다.

- **비동기 번역 (Azure Translator)**  
  Azure Translator API를 이용해 텍스트를 한국어로 번역합니다.  
  API 키는 `.env` 파일로 관리됩니다.

- **결과 저장 및 구조화**  
  결과를 JSON 형식으로 `03_output_results` 폴더에 저장합니다.  
  각 매거진마다 한 개의 JSON 파일이 생성됩니다.

- **임시 파일 정리**  
  번역이 끝난 후 `02_temp_images` 폴더가 자동 정리됩니다.

---

## 🧩 디렉터리 구조

```
magazinetranslator/
│
├── main.py                # 전체 파이프라인 오케스트레이션
├── ocr_processor.py       # EasyOCR 기반 텍스트 추출 및 문단 병합
├── api_clients.py         # Azure Translator API 호출
├── check_apis.py          # API 키 유효성 검사 스크립트
├── test_paddle_load.py    # PaddleOCR 환경 테스트
│
├── 01_input_zips/         # 입력 ZIP 파일 폴더
├── 02_temp_images/        # 임시 이미지 추출 폴더
└── 03_output_results/     # 번역 결과(JSON) 저장 폴더
```

---

## ⚙️ 설치 및 환경 설정

### 1. 필수 패키지 설치

```bash
pip install easyocr httpx python-dotenv torch opencv-python Pillow numpy
```

(추가적으로 GPU 사용 시 `paddlepaddle-gpu`, `paddleocr` 설치 필요)

### 2. 환경 변수 설정

`.env` 파일을 프로젝트 루트에 생성하고 다음 내용을 추가하세요:

```env
AZURE_TRANSLATOR_KEY=your_azure_key
AZURE_TRANSLATOR_ENDPOINT=https://api.cognitive.microsofttranslator.com
AZURE_TRANSLATOR_REGION=koreacentral
```

(옵션) Gemini API 테스트 시:
```env
GEMINI_API_KEY=your_gemini_key
```

---

## 🖥️ 사용 방법

1. 번역할 잡지 ZIP 파일을 `01_input_zips/` 폴더에 넣습니다.  
   (예: `weekly_magazine_2025_01.zip`)

2. 실행:
   ```bash
   python main.py
   ```

3. 완료 후 결과 JSON 파일이 `03_output_results/`에 생성됩니다.

---

## 🧾 출력 예시 (JSON 구조)

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
          "translated_text": "새로운 생활"
        }
      ]
    }
  ]
}
```

---

## 💡 참고

- EasyOCR과 Azure Translator API 호출은 비동기로 처리되어 성능을 최적화했습니다.  
- 모든 로그와 진행 상황은 콘솔에 출력됩니다.  
- OCR 모델 로딩 시 GPU를 자동 감지하며, GPU가 없을 경우 CPU 모드로 동작합니다.

---

## 🧑‍💻 제작자

**Developer:** Hyunmyung (Steve) Park  
**Purpose:** 개인 프로젝트 — 일본어 잡지 번역 자동화 도구
