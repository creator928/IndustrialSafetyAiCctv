"""
pip uninstall opencv-python
pip install opencv-python-headless
"""
import cv2
import numpy as np
from ultralytics import YOLO
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QTimer
import lap # track에 필요한 것
import time # 시간 측정

# region 글로벌 변수 선언
is_cam_connect = False  # 카메라 연결 확인 변수
model_yolo = YOLO("yolo11s.pt")  # YOLO11n 모델
fall_durations = {} # 추적 ID별로 fall 시작 시간 저장

# endregion 글로벌 변수 끝

# region 주요 함수 구현부
def printTest():
    print("Test complete!")

# 00. YOLO 기본 디텍션(이미지)
def yoloAllDetect(img):
    global model_yolo
    detected_result = model_yolo(img, verbose=False) # 모델 YOLO 기반 디텍팅 결과 저장
    detected_img = detected_result[0].plot()  # 결과를 시각화하여 프레임에 그리기
    return detected_img
# 00. 반환 : 디텍팅 된 이미지
# 01. YOLO 필터링 디텍션(이미지, 필터링 문자열 리스트)
def yoloFilterdDetect(img, filter_name):
    global model_yolo
    cls_names = model_yolo.names # YOLO에서 구분 가능한 클래시피케이션 리스트 호출
    detected_result = model_yolo(img, verbose=False) # 모델 YOLO 기반 디텍팅 결과 저장
    detected_img = img.copy() # 결과 이미지 저장용 img 복제
    for r in detected_result:
        box = r.boxes # 박스 정보 저장
        for b in box:
            conf = b.conf[0] * 100 # 해당 객체의 신뢰도 (백분률 전환)
            if conf > 50: # 신뢰도가 50이상일 때
                x1, y1, x2, y2 = b.xyxy[0]  # bounding box 시작xy, 끝xy whkvy
                cls_id = int(b.cls[0]) # 클래스 인덱스(YOLO 클래시피케이션 id)
                cls_name = cls_names[cls_id] # 클래스 id에 따른 name 가져옴
                if cls_name in filter_name: # 만약 필터링 리스트에 cls 네임이 있다면
                    detct_info = f"{cls_name} ({conf:.2f}%)"
                    if cls_name == "person":
                        cv2.rectangle(detected_img, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                        cv2.putText(detected_img, detct_info, (int((x1+x2)//2*0.85), int(y1)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 10)
                        cv2.putText(detected_img, detct_info, (int((x1+x2)//2*0.85), int(y1)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
                    else:
                        cv2.rectangle(detected_img, (int(x1), int(y1)), (int(x2), int(y2)), (255, 50, 50), 2)
                        cv2.putText(detected_img, detct_info, (int((x1+x2)//2*0.85), int(y1)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 10)
                        cv2.putText(detected_img, detct_info, (int((x1+x2)//2*0.85), int(y1)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    return detected_img
# 01. 반환 : 디텍팅 된 이미지
# 02. YOLO person 디텍션 & 크롭(이미지, 필터링 문자열 리스트)
def yoloPersonDetect(img):
    global model_yolo
    cropped_bbxy = [] # [x1, y1, x2, y2]를 리스트로 저장
    cropped_img = [] # [x1, y1, x2, y2]로 자른 이미지들 저장
    cls_names = model_yolo.names # YOLO에서 구분 가능한 클래시피케이션 리스트 호출
    detected_result = model_yolo(img, verbose=False) # 모델 YOLO 기반 디텍팅 결과 저장
    detected_img = img.copy() # 결과 이미지 저장용 img 복제
    for r in detected_result:
        box = r.boxes # 박스 정보 저장
        for b in box:
            conf = b.conf[0] * 100 # 해당 객체의 신뢰도 (백분률 전환)
            if conf > 50: # 신뢰도가 50이상일 때
                x1, y1, x2, y2 = b.xyxy[0]  # bounding box 시작xy, 끝xy whkvy
                # 바운딩 박스 좌표 저장 xyxy
                cropped_bbxy.append([int(x1), int(y1), int(x2), int(y2)])
                # 바운딩 박스 영역으로 이미지를 크롭
                cropped_img.append(img[int(y1):int(y2), int(x1):int(x2)])
                cls_id = int(b.cls[0]) # 클래스 인덱스(YOLO 클래시피케이션 id)
                cls_name = cls_names[cls_id] # 클래스 id에 따른 name 가져옴
                if cls_name == "person":
                    detct_info = f"Person ({conf:.2f}%)" # 출력 정보
                    cv2.rectangle(detected_img, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                    cv2.putText(detected_img, detct_info, (int((x1+x2)//2*0.85), int(y1)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 10)
                    cv2.putText(detected_img, detct_info, (int((x1+x2)//2*0.85), int(y1)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    return detected_img, cropped_img, cropped_bbxy
# 02. 반환 : 디텍팅 된 이미지, 크롭된 이미지 리스트, 크롭을 한 좌표
# 03. fall 디텍션
def yoloFallDetect(img):
    global model_yolo
    global fall_durations # 넘어진 시간 저장용 딕셔너리
    cropped_bbxy = [] # [x1, y1, x2, y2]를 리스트로 저장
    cls_names = model_yolo.names # YOLO에서 구분 가능한 클래시피케이션 리스트 호출
    detected_result = model_yolo.track(img, verbose=False, persist=True) # persist 옵션을 통해 추적
    detected_img = img.copy() # 결과 이미지 저장용 img 복제
    for r in detected_result:
        box = r.boxes
        for b in box:
            conf = b.conf[0] * 100 # 해당 객체의 신뢰도 (백분률 전환)
            if conf > 50: # 신뢰도가 50이상일 때
                x1, y1, x2, y2 = b.xyxy[0]  # bounding box 시작xy, 끝xy whkvy
                cls_id = int(b.cls[0]) # 클래스 인덱스(YOLO 클래시피케이션 id)
                cls_name = cls_names[cls_id] # 클래스 id에 따른 name 가져옴
                obj_id = int(b.id[0]) # 객체의 id(동일 객체 추적)
                detct_info = f"{cls_name} ({conf:.2f}%)" # 출력 정보
                if cls_name == "bottle": # 넘어짐 대상 person
                    person_h = y2 - y1 # 높이
                    person_w = x2 - x1 # 너비
                    person_thr = person_h - person_w # 높이 - 너비 스레스홀드
                    current_time = time.time() # 현재시간 호출
                    if person_thr <= 0: # 스레스홀드가 음수일 경우
                        if obj_id not in fall_durations: # 글로벌 변수 딕셔너리에 id가 없을 경우
                            fall_durations[obj_id] = current_time # 현재 시간을 id에 맞춰 저장
                        fall_due = current_time - fall_durations[obj_id]
                        #print(obj_id, fall_durations, current_time)
                        if fall_due >= 5:
                            color = (0, 0, 255)
                        elif fall_due >= 2:
                            color = (0, 255, 255)
                        else:
                            color = (0, 255, 0)
                    else:
                        if obj_id in fall_durations:
                            del fall_durations[obj_id]
                        color = (0, 255, 0)
                    cv2.rectangle(detected_img, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                    cv2.putText(detected_img, detct_info, (int((x1+x2)//2*0.85), int(y1)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 10)
                    cv2.putText(detected_img, detct_info, (int((x1+x2)//2*0.85), int(y1)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
                else:
                    cv2.rectangle(detected_img, (int(x1), int(y1)), (int(x2), int(y2)), (255, 50, 50), 2)
                    cv2.putText(detected_img, detct_info, (int((x1+x2)//2*0.85), int(y1)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 10)
                    cv2.putText(detected_img, detct_info, (int((x1+x2)//2*0.85), int(y1)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    return detected_img
# 03. 반환 : 

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
                is_cam_connect = False
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

        test_imglist = []
        test_xylist = []
        if ret:
            # TODO 여기서 영상처리 함수를 호출하여 사용

            #frame = yoloAllDetect(frame)
            #frame = yoloFilterdDetect(frame, ["person", "bottle", "cell phone"])
            #frame, test_imglist, test_xylist = yoloPersonDetect(frame)
            frame = yoloFallDetect(frame)
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
