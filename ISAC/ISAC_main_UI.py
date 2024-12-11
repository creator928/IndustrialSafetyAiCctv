import cv2 # opencv-python-headless 버전 설치 요망
import numpy as np
from ultralytics import YOLO
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QTimer

# region 글로벌 변수 선언
is_cam_connect = False  # 카메라 연결 확인 변수
model_yolo = YOLO("yolo11s.pt")  # YOLO11n 모델
# endregion 글로벌 변수 끝

# region 주요 함수 구현부
def printTest():
    print("Test complete!")

# 00. YOLO 기본 디텍션(이미지)
def yoloAllDetect(img):
    global model_yolo
    detected_result = model_yolo(img) # 모델 YOLO 기반 디텍팅 결과 저장
    detected_img = detected_result[0].plot()  # 결과를 시각화하여 프레임에 그리기
    return detected_img
# 00. 반환 : 디텍팅 된 이미지
# endregion 주요 함수 구현부

# region 메인 윈도우 클래스 정의
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # UI 초기화
        self.initUI()
        # UI 출력
        self.show()

    def initUI(self):
        # 메인 윈도우 설정
        self.setWindowTitle("ISAC GUI")
        self.setGeometry(100, 100, 1600, 1000)  # 시작x, 시작y, width, height

        # 카메라 출력용 레이블
        self.camdisplay_label = QLabel(self)
        self.camdisplay_label.setGeometry(50, 50, 640, 480)  # 시작x, 시작y, width, height
        # 이미지 초기화
        width, height = 640, 480
        blank_image = QImage(width, height, QImage.Format_RGB32)
        blank_image.fill(Qt.black)
        # QLabel에 빈 이미지 설정
        pixmap = QPixmap.fromImage(blank_image)
        self.camdisplay_label.setPixmap(pixmap)
        # QLabel의 가운데 정렬 설정
        self.camdisplay_label.setAlignment(Qt.AlignCenter)

        # 카메라 오픈 버튼 생성
        self.camopen_button = QPushButton("Camera Open", self)
        self.camopen_button.setGeometry(50, 600, 200, 50)  # 시작x, 시작y, width, height
        # 버튼 클릭 시 카메라 테스트 진행
        self.camopen_button.clicked.connect(self.cameraTest)

        # 

    def cameraTest(self):
        # 카메라 열렸는지 확인
        global is_cam_connect
        if not is_cam_connect: # 카메라가 False 상태의 경우, 카메라 영상 가져오기
            is_cam_connect = True
            # opencv로 웹캠 열기
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                print("Can not open the camera!")
                return
            # 프레임 업데이트 타이머 설정
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.update_frame) # 프레임 업데이트 호출
            self.timer.start(30)
        else: # 카메라가 True 상태의 경우, 카메라 정지, 릴리즈
            is_cam_connect = False
            self.timer.stop()
            self.cap.release()
        
    def update_frame(self):
        # VideoCapture로부터 프레임을 가져옴
        ret, frame = self.cap.read()
        if ret:
            # TODO 여기서 영상처리 함수를 호출하여 사용

            frame = yoloAllDetect(frame)

            # TODO 영상처리 종료

            # 이미지 출력 시작
            # 이미지를 RGB 형식으로 변환
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # numpy 배열을 QImage로 변환
            h, w, ch = frame.shape # 프레임 h, w, 채널
            bytes_per_line = ch * w
            qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            # QImage를 QPixmap으로 변환 후 QLabel에 설정
            pixmap = QPixmap.fromImage(qimg)
            # QLabel에 이미지 출력
            self.camdisplay_label.setPixmap(pixmap)
            # 이미지 출력 완료
        else:
            print("Can not read the frame!")
    def closeEvent(self, event):
        # 창 닫을 때 웹캠 해제 및 타이머 정지
        self.timer.stop()
        self.cap.release()
        event.accept()
# endregion 메인 윈도우 클래스 정의

if __name__ == "__main__":
    # QApplication 생성
    app = QApplication(sys.argv)
    # 메인 윈도우 생성
    main_window = MainWindow()
    main_window.show()
    # 이벤트 루프 실행
    sys.exit(app.exec_())
