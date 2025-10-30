# test_paddle_load.py
import sys
print("Python Executable:", sys.executable)

try:
    import paddle
    import paddleocr
    print(f"PaddlePaddle Version: {paddle.__version__}")
    print(f"PaddleOCR Version: {paddleocr.__version__}")

    print("--- PaddlePaddle Diagnostics ---")
    gpu_available = paddle.is_compiled_with_cuda()
    print(f"CUDA Compiled: {gpu_available}")
    gpu_count = 0
    if gpu_available:
        gpu_count = paddle.device.cuda.device_count()
        print(f"GPU Count: {gpu_count}")
        if gpu_count > 0:
            gpu_name = paddle.device.cuda.get_device_name(0)
            print(f"GPU Name (Device 0): {gpu_name}")
        else:
            print("No GPU devices found by PaddlePaddle.")
    else:
        print("PaddlePaddle was not compiled with CUDA support.")
    print("----------------------------\n")

    print("Attempting PaddleOCR init (using use_textline_orientation, no explicit GPU)...")
    # --- [REVISED INITIALIZATION] ---
    # 1. Replace deprecated 'use_angle_cls' with 'use_textline_orientation'
    # 2. Omit 'use_gpu' - let paddlepaddle-gpu try to auto-detect
    ocr = paddleocr.PaddleOCR(use_textline_orientation=True, lang='ch')
    # --- [END REVISED INITIALIZATION] ---

    print("PaddleOCR init SUCCESSFUL")
    print("Checking if GPU is actually being used...")
    # A simple way to check if paddle thinks it's using GPU
    try:
        current_place = paddle.get_device()
        print(f"PaddlePaddle is currently using device: {current_place}")
        if 'gpu' in current_place.lower():
            print("✅ GPU appears to be active!")
        else:
            print("⚠️ GPU does not appear to be active (CPU fallback?).")
    except Exception as device_e:
        print(f"Could not determine active device: {device_e}")


except Exception as e:
    print(f"ERROR during import or init: {e}")

input("Press Enter to exit...")