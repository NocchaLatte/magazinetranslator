# ocr_processor.py

import easyocr
from PIL import Image
from pathlib import Path
from typing import List, Dict, Union
import numpy as np
import os
from dotenv import load_dotenv
import torch
import cv2

load_dotenv()

# --- 1. EasyOCR 모델 로드 ---
reader = None # 전역 변수로 선언
try:
    gpu_available = torch.cuda.is_available()
    print(f"✅ [EasyOCR] PyTorch CUDA 사용 가능: {gpu_available}")
    print("✅ [EasyOCR] 모델 로드 시도 ('ja', 'en' 언어, GPU 사용)...")
    reader = easyocr.Reader(['ja', 'en'], gpu=gpu_available)
    print("✅ [EasyOCR] 모델 로드가 완료되었습니다.")
except Exception as e:
    print(f"🚨 [치명적 오류] EasyOCR 모델 로드 실패: {e}")
    reader = None

def _convert_easyocr_box(bbox):
    """EasyOCR bbox를 [x, y, w, h]로 변환"""
    try:
        points = np.array(bbox, dtype=np.int32)
        min_x = np.min(points[:, 0])
        min_y = np.min(points[:, 1])
        max_x = np.max(points[:, 0])
        max_y = np.max(points[:, 1])
        box = [int(min_x), int(min_y), int(max_x - min_x), int(max_y - min_y)]
        return box
    except Exception:
        return [0, 0, 0, 0]

# --- [신규] 문단 병합 함수 ---
def _group_lines_into_paragraphs(lines: List[Dict], max_vertical_gap_ratio: float = 0.5) -> List[Dict]:
    """
    EasyOCR의 줄 단위 결과를 세로 간격을 기준으로 문단으로 병합합니다.
    Args:
        lines: [{'box': [x,y,w,h], 'text': '...'}, ...] 형태의 줄 리스트
        max_vertical_gap_ratio: 줄 높이 대비 최대 허용 세로 간격 비율 (예: 0.5 = 줄 높이의 50%)
    Returns:
        병합된 문단 리스트 [{'box': [x,y,w,h], 'text': '...'}, ...]
    """
    if not lines:
        return []

    # y좌표 기준으로 줄 정렬 (위에서 아래로)
    lines.sort(key=lambda item: item['box'][1])

    paragraphs = []
    current_paragraph_lines = []

    for i, line in enumerate(lines):
        line_box = line['box']
        line_text = line['text']
        line_y, line_h = line_box[1], line_box[3]

        if not current_paragraph_lines:
            # 첫 줄이거나 새 문단 시작
            current_paragraph_lines.append(line)
        else:
            # 이전 줄과 비교하여 병합 여부 결정
            prev_line = current_paragraph_lines[-1]
            prev_box = prev_line['box']
            prev_y, prev_h = prev_box[1], prev_box[3]

            # 세로 간격 계산
            vertical_gap = line_y - (prev_y + prev_h)
            # 이전 줄 높이의 일정 비율 이하 간격이면 같은 문단으로 간주
            max_allowed_gap = prev_h * max_vertical_gap_ratio

            if vertical_gap <= max_allowed_gap:
                # 같은 문단으로 병합
                current_paragraph_lines.append(line)
            else:
                # 새 문단 시작 -> 이전까지의 문단 정보 확정 및 저장
                # 1. 문단 텍스트 조합 (일본어는 줄바꿈 없이 이어붙임)
                para_text = "".join(p_line['text'] for p_line in current_paragraph_lines)
                # 2. 문단 전체 경계 상자 계산
                min_x = min(p_line['box'][0] for p_line in current_paragraph_lines)
                min_y = min(p_line['box'][1] for p_line in current_paragraph_lines)
                max_x = max(p_line['box'][0] + p_line['box'][2] for p_line in current_paragraph_lines)
                max_y = max(p_line['box'][1] + p_line['box'][3] for p_line in current_paragraph_lines)
                para_box = [int(min_x), int(min_y), int(max_x - min_x), int(max_y - min_y)]

                paragraphs.append({'box': para_box, 'text': para_text})

                # 현재 줄로 새 문단 시작
                current_paragraph_lines = [line]

    # 마지막 문단 처리
    if current_paragraph_lines:
        para_text = "".join(p_line['text'] for p_line in current_paragraph_lines)
        min_x = min(p_line['box'][0] for p_line in current_paragraph_lines)
        min_y = min(p_line['box'][1] for p_line in current_paragraph_lines)
        max_x = max(p_line['box'][0] + p_line['box'][2] for p_line in current_paragraph_lines)
        max_y = max(p_line['box'][1] + p_line['box'][3] for p_line in current_paragraph_lines)
        para_box = [int(min_x), int(min_y), int(max_x - min_x), int(max_y - min_y)]
        paragraphs.append({'box': para_box, 'text': para_text})

    return paragraphs


def extract_structured_data(image_path: Path) -> List[Dict[str, Union[str, List[int]]]]:
    """
    하나의 이미지 파일에서 구조화된 OCR 데이터(문단 리스트)를 추출합니다.
    EasyOCR로 줄 단위 추출 후 문단으로 병합합니다.
    """
    if reader is None:
        raise RuntimeError("EasyOCR 모델(Reader)이 로드되지 않았습니다.")

    try:
        # --- 1. 이미지 로드 ---
        img_bytes = np.fromfile(image_path, dtype=np.uint8)
        img_cv = cv2.imdecode(img_bytes, cv2.IMREAD_COLOR)
        if img_cv is None:
            raise ValueError(f"OpenCV could not decode image: {image_path.name}")

        # --- 2. EasyOCR 실행 (줄 단위) ---
        result = reader.readtext(img_cv, detail=1, paragraph=False)

        if not result:
            return []

        # --- 3. [수정] 줄 단위 결과를 파싱하여 리스트로 변환 ---
        extracted_lines = []
        for (bbox, text, prob) in result:
            if prob < 0.40: # 신뢰도 필터링
                continue
            box_xywh = _convert_easyocr_box(bbox)
            # 텍스트가 비어있지 않은 경우만 추가
            if text.strip():
                extracted_lines.append({
                    'box': box_xywh,
                    'text': text.strip()
                })

        # --- 4. [신규] 줄들을 문단으로 병합 ---
        processed_paragraphs = _group_lines_into_paragraphs(extracted_lines)

        return processed_paragraphs # 최종 문단 리스트 반환

    except Exception as e:
        print(f"🚨 [OCR 오류] {image_path.name} 처리 중 오류 발생: {e}")
        return []