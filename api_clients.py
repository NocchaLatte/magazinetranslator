# api_clients.py

import os
import httpx  # 'requests'의 비동기 버전
import uuid # Azure API 호출 시 필요



# --- 2단계: Azure Translator (번역) 클라이언트 ---

# .env에서 Azure 설정 가져오기
AZURE_TRANSLATOR_KEY = os.getenv("AZURE_TRANSLATOR_KEY")
AZURE_TRANSLATOR_ENDPOINT = os.getenv("AZURE_TRANSLATOR_ENDPOINT")
AZURE_TRANSLATOR_REGION = os.getenv("AZURE_TRANSLATOR_REGION")

async def call_azure_translation(session: httpx.AsyncClient, text_to_translate: str) -> str:
    """
    검증된 텍스트를 받아 Azure Translator API로 번역합니다. (비동기)
    'session'을 매개변수로 받아 커넥션 풀을 재사용합니다.
    """
    if not all([AZURE_TRANSLATOR_KEY, AZURE_TRANSLATOR_ENDPOINT, AZURE_TRANSLATOR_REGION]):
        return "[Azure 오류: .env 설정 누락]"
        
    if not text_to_translate.strip():
        return "" # 빈 텍스트는 요청하지 않음

    # API 엔드포인트 및 헤더 구성
    constructed_url = AZURE_TRANSLATOR_ENDPOINT.rstrip('/') + '/translate'
    params = {
        'api-version': '3.0',
        'from': 'ja',
        'to': 'ko'
    }
    headers = {
        'Ocp-Apim-Subscription-Key': AZURE_TRANSLATOR_KEY,
        'Ocp-Apim-Subscription-Region': AZURE_TRANSLATOR_REGION,
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4()) # 요청 추적을 위한 ID
    }
    body = [{'text': text_to_translate}]

    try:
        # 비동기 POST 요청
        response = await session.post(constructed_url, params=params, headers=headers, json=body)
        
        response.raise_for_status() # 4xx, 5xx 오류가 발생하면 예외를 일으킴
        
        # 번역 결과 파싱
        result_json = response.json()
        return result_json[0]['translations'][0]['text']

    except httpx.HTTPStatusError as e:
        print(f"🚨 [Azure 오류] API가 오류 상태 코드를 반환: {e.response.status_code} - {e.response.text}")
        return f"[Azure 오류: {e.response.status_code}]"
    except Exception as e:
        print(f"🚨 [Azure 오류] API 호출 중 예외 발생: {e}")
        return f"[Azure 오류: {e}]"