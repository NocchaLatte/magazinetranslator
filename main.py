# main.py

import os
import asyncio
import zipfile
import glob
import shutil
import json        # <-- [추가] JSON 저장을 위해 임포트
import httpx       # <-- [추가] 비동기 HTTP 클라이언트
from pathlib import Path
from dotenv import load_dotenv

# --- 1. 모듈 임포트 ---
try:
    import ocr_processor
    import api_clients
except ImportError as e:
    print(f"🚨 [치명적 오류] 모듈 임포트 실패: {e}")
    print("   'ocr_processor.py'와 'api_clients.py' 파일이 'main.py'와 같은 폴더에 있는지 확인하세요.")
    exit()

# --- 2. 설정 및 환경 변수 로드 ---
load_dotenv()
# (api_clients.py에서 이미 키를 로드했지만, main에서도 경로 확인용으로 로드)

# 동시성 제어 (한 번에 5개의 페이지만 동시에 처리)
# CPU 코어 수나 API 제한에 맞춰 조절하세요.
SEMAPHORE = asyncio.Semaphore(2)

# --- 3. 경로 설정 ---
BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "01_input_zips"
TEMP_DIR = BASE_DIR / "02_temp_images"
OUTPUT_DIR = BASE_DIR / "03_output_results"

# --- 4. 0단계: ZIP 압축 해제 및 파일 준비 ---
def setup_directories_and_unzip():
    print("--- 0단계: 폴더 설정 및 ZIP 압축 해제 시작 ---")
    INPUT_DIR.mkdir(exist_ok=True)
    TEMP_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    zip_files = list(INPUT_DIR.glob("*.zip"))
    
    if not zip_files:
        print(f"  [알림] {INPUT_DIR} 폴더에 처리할 .zip 파일이 없습니다.")
        return [], {} # 빈 리스트와 빈 딕셔너리 반환

    print(f"  [발견] {len(zip_files)}개의 ZIP 파일 발견.")
    
    all_image_paths = []
    # [추가] 원본 zip(매거진)별로 결과물을 저장하기 위한 딕셔너리
    # { 'magazine_A': [img1_path, img2_path], 'magazine_B': [img3_path] }
    magazine_map = {}

    for zip_path in zip_files:
        magazine_name = zip_path.stem 
        unzip_target_dir = TEMP_DIR / magazine_name
        unzip_target_dir.mkdir(exist_ok=True)
        print(f"  -> '{zip_path.name}' 압축 해제 중... -> {unzip_target_dir}")
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(unzip_target_dir)
            
            image_extensions = ["*.jpg", "*.jpeg", "*.png"]
            images_in_this_zip = []
            for ext in image_extensions:
                images_in_this_zip.extend(unzip_target_dir.rglob(ext))
            
            images_in_this_zip.sort() # 페이지 순서 정렬
            
            print(f"     ... {len(images_in_this_zip)}개의 이미지 파일 발견.")
            all_image_paths.extend(images_in_this_zip)
            # [추가] 매거진 맵에 추가
            magazine_map[magazine_name] = images_in_this_zip

        except Exception as e:
            print(f"  🚨 [오류] '{zip_path.name}' 처리 중 오류 발생: {e}")

    print(f"--- 0단계 완료: 총 {len(all_image_paths)}개의 이미지를 처리합니다. ---\n")
    return all_image_paths, magazine_map


# --- 5. [수정] 비동기 파이프라인 (완성) ---
async def process_page(session: httpx.AsyncClient, image_path: Path):
    """
    단일 이미지 페이지 파이프라인 (PaddleOCR -> Azure 번역)
    [수정] Gemini 검증 단계가 제거되었습니다. // 나중에 더 좋은 방법을 찾아볼 예정
    """
    
    # [수정] Semaphore 값을 다시 5 (또는 그 이상)로 돌려도 됩니다.
    # GPU가 병목이므로 CPU 코어 수에 맞춰 2~4 정도로 테스트해 보세요.
    async with SEMAPHORE: # 👈 main.py 상단의 이 값을 4 정도로 수정하세요
        print(f"[OCR 시작] {image_path.name}")
        
        # --- 1단계: OCR (PaddleOCR, 별도 스레드에서 실행) ---
        try:
            structured_data = await asyncio.to_thread(
                ocr_processor.extract_structured_data, 
                image_path
            )
        except Exception as e:
            print(f"🚨 [OCR 오류] {image_path.name} 처리 중 심각한 오류: {e}")
            return (image_path, [])

        if not structured_data:
            print(f"[OCR 완료] {image_path.name}: 추출된 텍스트 블록이 없습니다.")
            return (image_path, [])
        
        print(f"[OCR 완료] {image_path.name}: {len(structured_data)}개의 텍스트 블록 발견.")
        
        processed_blocks_output = [] # 최종 결과(번역된 블록)를 담을 리스트

        # --- [수정] 2단계: 번역 (Gemini 없이 바로 번역) ---
        
        for i, block in enumerate(structured_data):
            original_text = block['text']
            box = block['box']
            
            if not original_text.strip():
                continue
            
            print(f"  -> {image_path.name} [블록 {i+1}/{len(structured_data)}] 번역 중...")
            
            # [제거] 1.5. Gemini 검증 (삭제됨)
            
            # 2. Azure 번역 (원본 텍스트를 바로 번역)
            translated_text = await api_clients.call_azure_translation(session, original_text)
            
            # [제거] Gemini 31초 대기 (삭제됨)
            
            # [유지] Azure 속도 제한 (0.5초 또는 1초 대기)
            # (PaddleOCR이 Tesseract보다 블록을 훨씬 잘 묶어주므로
            # 호출 횟수가 줄어, 이 대기 시간도 0.2초 등으로 줄여도 됩니다.)
            await asyncio.sleep(0.5) 

            # 3. 결과 저장
            processed_blocks_output.append({
                'box': box,
                'original_text': original_text,
                'clean_text': original_text, # 원본 = 깨끗한 텍스트
                'translated_text': translated_text
            })

        print(f"✅ [처리 완료] {image_path.name}")
        return (image_path, processed_blocks_output)
    
# --- 6. [신규] 3단계: 결과 저장 ---

def save_results(magazine_map: dict, all_page_results: list):
    """
    모든 처리 결과를 매거진별 JSON 파일로 03_output_results에 저장합니다.
    """
    print("\n--- 3단계: 최종 결과 저장 시작 ---")
    
    # (이미지 경로, 블록 리스트) 튜플 리스트를 딕셔너리로 변환 (빠른 조회용)
    # { 'img1_path': [...], 'img2_path': [...] }
    results_dict = dict(all_page_results)
    
    for magazine_name, image_paths in magazine_map.items():
        # 이 매거진의 최종 JSON 구조
        output_data = {
            'magazine_name': magazine_name,
            'total_pages': len(image_paths),
            'pages': []
        }
        
        print(f"  -> '{magazine_name}' 결과 취합 중...")
        
        # 정렬된 이미지 경로(페이지 순서)를 순회
        for i, img_path in enumerate(image_paths):
            page_data = {
                'page_number': i + 1,
                'original_filename': img_path.name,
                'blocks': results_dict.get(img_path, []) # process_page 결과 가져오기
            }
            output_data['pages'].append(page_data)
            
        # 매거진별로 하나의 JSON 파일 생성
        output_filename = OUTPUT_DIR / f"{magazine_name}_translated.json"
        
        try:
            with open(output_filename, 'w', encoding='utf-8') as f:
                # ensure_ascii=False로 한글이 깨지지 않게 저장
                # indent=2로 가독성 높게 저장
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            print(f"  ✅ [저장 성공] {output_filename}")
        except Exception as e:
            print(f"  🚨 [저장 오류] {output_filename} 저장 중 오류 발생: {e}")

    print("--- 3단계 완료 ---")


# --- 7. 4단계: 임시 파일 정리 ---
def cleanup_temp_files():
    print(f"\n--- 4단계: 임시 파일 정리 시작 ---")
    if not TEMP_DIR.exists():
        return
    try:
        shutil.rmtree(TEMP_DIR)
        print(f"  ✅ [성공] {TEMP_DIR} 폴더와 모든 하위 파일을 삭제했습니다.")
        TEMP_DIR.mkdir(exist_ok=True)
    except OSError as e:
        print(f"  🚨 [오류] {TEMP_DIR} 폴더 삭제 중 오류 발생: {e}")


# --- 8. [수정] 메인 실행 함수 (오케스트레이터) ---

async def main():
    """메인 비동기 실행 함수 (오케스트레이터)"""
    
    image_paths_to_process = []
    magazine_map = {}
    all_page_results = []

    try:
        # 0단계: 폴더 준비 및 압축 해제
        image_paths_to_process, magazine_map = setup_directories_and_unzip()
        
        if not image_paths_to_process:
            print("처리할 이미지가 없습니다. 스크립트를 종료합니다.")
            return

        print(f"\n--- 1/2단계: OCR, 검증, 번역 작업 동시 시작 (총 {len(image_paths_to_process)}개) ---")

        # httpx.AsyncClient 세션을 생성하여 커넥션 풀을 재사용 (속도 향상)
        async with httpx.AsyncClient(timeout=30.0) as session:
            # 비동기 작업 목록 생성
            tasks = []
            for img_path in image_paths_to_process:
                tasks.append(process_page(session, img_path))
            
            # asyncio.gather를 사용해 모든 작업을 "동시에" (최대 5개씩) 실행
            # all_page_results: [(img_path, [block_data, ...]), ...]
            all_page_results = await asyncio.gather(*tasks)

        print("\n--- 모든 페이지 처리 완료 ---")
        
        # 3단계: 결과 파일로 저장
        if magazine_map and all_page_results:
            save_results(magazine_map, all_page_results)
        else:
            print("[알림] 처리된 결과가 없어 저장을 건너뜁니다.")


    except Exception as e:
        print(f"🚨 [치명적 오류] 메인 작업 실행 중 오류 발생: {e}")
    
    finally:
        # 4단계: 임시 파일 정리
        cleanup_temp_files()


if __name__ == "__main__":
    print("=========================================")
    print("   매거진 번역 자동화 스크립트 시작")
    print("=========================================\n")
    asyncio.run(main())
    print("\n=========================================")
    print("   모든 작업 완료. 스크립트 종료.")
    print("=========================================")