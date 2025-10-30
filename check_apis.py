import os
import requests
from dotenv import load_dotenv

def check_gemini():
    """Gemini API 키가 유효한지, 'generate_content'를 테스트합니다."""
    print("--- 1. Gemini API 테스트 시작 ---")
    try:
        gemini_key = os.getenv("GEMINI_API_KEY")
        if not gemini_key:
            print("🚨 [오류] .env 파일에 GEMINI_API_KEY가 없습니다.")
            return
        
        # ----------------------------------------------------
        # [수정] 방금 확인한 목록에 있는 모델 이름으로 지정
        model_name = 'models/gemini-2.5-pro' 
        print(f"... 모델 '{model_name}'에 연결 시도 ...")
        model = genai.GenerativeModel(model_name)
        # ----------------------------------------------------

        # 간단한 generate_content 테스트
        response = model.generate_content("Hello", stream=False)
        
        # 응답 객체에서 'text' 속성에 접근
        if response.text and len(response.text) > 0:
             print(f"✅ [성공] Gemini API가 성공적으로 응답했습니다. (응답: {response.text[:20]}...)")
        else:
             print("🚨 [오류] Gemini API 응답이 비어있습니다.")
             print(f"   전체 응답 객체: {response}")
             
    except Exception as e:
        print(f"🚨 [오류] Gemini API 테스트 중 예외 발생: {e}")
    print("-" * 30 + "\n")


def check_azure_translator():
    """Azure Translator API 키와 엔드포인트가 유효한지 테스트합니다."""
    print("--- 2. Azure Translator API 테스트 시작 ---")
    try:
        azure_key = os.getenv("AZURE_TRANSLATOR_KEY")
        azure_endpoint = os.getenv("AZURE_TRANSLATOR_ENDPOINT")
        azure_region = os.getenv("AZURE_TRANSLATOR_REGION")

        if not all([azure_key, azure_endpoint, azure_region]):
            print("🚨 [오류] .env 파일에 Azure 키, 엔드포인트 또는 리전이 누락되었습니다.")
            return

        # '지원 언어' API 호출 (가벼운 테스트)
        path = '/languages?api-version=3.0'
        constructed_url = azure_endpoint.rstrip('/') + path

        headers = {
            'Ocp-Apim-Subscription-Key': azure_key,
            'Ocp-Apim-Subscription-Region': azure_region,
            'Content-type': 'application/json'
        }
        
        print(f"... {constructed_url} (리전: {azure_region}) 호출 시도 ...")
        response = requests.get(constructed_url, headers=headers, timeout=10) # 타임아웃 추가
        
        if response.status_code == 200:
            print(f"✅ [성공] Azure Translator API가 성공적으로 응답했습니다. (상태 코드: {response.status_code})")
        else:
            print(f"🚨 [오류] Azure Translator API가 오류를 반환했습니다. (상태 코드: {response.status_code})")
            print(f"   응답 내용: {response.text}")

    except requests.exceptions.Timeout:
        print("🚨 [오류] Azure Translator API 요청 시간이 초과되었습니다.")
    except Exception as e:
        print(f"🚨 [오류] Azure Translator API 테스트 중 예외 발생: {e}")
    print("-" * 30 + "\n")


def main():
    load_dotenv()
    print("... .env 파일 로드 완료 ...\n")
    check_gemini()
    check_azure_translator()

if __name__ == "__main__":
    main()