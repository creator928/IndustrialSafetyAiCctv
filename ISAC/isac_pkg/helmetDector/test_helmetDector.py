import tkinter as tk
from tkinter import filedialog
from helmetDector import ISAC_DectHelmet
import cv2

def main():
    # HelmetDetector 클래스 인스턴스 생성
    helmet_detector = ISAC_DectHelmet()

    # Tkinter 파일 다이얼로그를 사용하여 이미지 선택
    root = tk.Tk()
    root.withdraw()  # Tkinter 메인 윈도우 숨기기

    file_types = [
        ("JPEG files", "*.jpg"),
        ("PNG files", "*.png"),
        ("All files", "*.*")
    ]

    test_image_path = filedialog.askopenfilename(title="테스트할 이미지를 선택하세요", filetypes=file_types)

    if not test_image_path:
        print("이미지가 선택되지 않았습니다.")
        return

    # 선택된 이미지 경로로 작업
    work_info = helmet_detector.process_image(test_image_path)

    # 결과 출력
    if work_info and not isinstance(work_info, dict):
        print("Detected workers:")
        for worker in work_info:
            print(worker)
    else:
        print("No workers detected or no matching helmet color found.")

if __name__ == "__main__":
    main()
