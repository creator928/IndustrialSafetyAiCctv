import cv2
import numpy as np
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QFileDialog, QCheckBox, QWidget, QMessageBox
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QTimer
import time # 시간 측정

from isac_pkg.fallDetector.fallDector import ISAC_FallDetector
from isac_pkg.helpDetector.helpDetector import ISAC_HelpDetector
from isac_pkg.fireDetector.fireDetector import ISAC_FireDetector

# 이건 옮길 때 필요 없음
from isac_pkg.ISACdetector import ISAC

# region 글로벌 변수 선언
is_cam_connect = False  # 카메라 연결 확인 변수
fall_durations = {} # 추적 ID별로 fall 시작 시간 저장
# endregion 글로벌 변수 끝


# region 메인 윈도우 클래스 정의
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # ISAC 패키지 클래스 선언
        #self.isac = ISAC()
        self.isacfall = ISAC_FallDetector()
        self.isachelp = ISAC_HelpDetector()
        self.isacfire = ISAC_FireDetector()

        # UI 초기화
        self.initUI()
        # UI 출력
        self.show()

    def initUI(self):
        # 메인 윈도우 설정
        self.setWindowTitle("ISAC GUI")
        self.setGeometry(100, 100, 2500, 1200)  # 시작x, 시작y, width, height

        # 카메라 출력용 레이블
        self.camdisplay_label = QLabel(self)
        self.camdisplay_label.setGeometry(25, 100, 800, 600)  # 시작x, 시작y, width, height
        # 이미지 초기화
        width, height = 800, 600
        blank_image = QImage(width, height, QImage.Format_RGB32)
        blank_image.fill(Qt.black)
        # QLabel에 빈 이미지 설정
        pixmap = QPixmap.fromImage(blank_image)
        self.camdisplay_label.setPixmap(pixmap)
        # QLabel의 가운데 정렬 설정
        self.camdisplay_label.setAlignment(Qt.AlignCenter)

        # 카메라 오픈 버튼 생성
        self.camopen_button = QPushButton("Camera Open", self)
        self.camopen_button.setGeometry(25, 25, 200, 50)  # 시작x, 시작y, width, height
        # 버튼 클릭 시 카메라 테스트 진행
        self.camopen_button.clicked.connect(self.cameraTest)

        # 비디오 오픈 버튼 생성
        self.videoopen_button = QPushButton("Video Open", self)
        self.videoopen_button.setGeometry(850, 25, 200, 50)  # 시작x, 시작y, width, height
        # 버튼 클릭 시 비디오 테스트 진행
        self.videoopen_button.clicked.connect(self.videoTest)

        # 현재 시간 표시용 
        self.date_label = QLabel("Date : ", self)
        # 텍스트 크기 조정
        self.date_label.setStyleSheet("font-size: 30px;")  # 원하는 크기로 조정
        self.date_label.setGeometry(10, 1150, 450, 50)
        # 타이머 설정 (1초마다 업데이트)
        self.date_timer = QTimer(self)
        self.date_timer.timeout.connect(self.updateDate)
        self.date_timer.start(1000)  # 1000ms = 1초
        self.updateDate()
        # 캡처 및 세이브 버튼
        self.date_button = QPushButton("Date Save", self)
        self.date_button.setGeometry(450, 1150, 200, 50)  # 시작x, 시작y, width, height
        # 버튼 클릭 시 카메라 테스트 진행
        self.date_button.clicked.connect(self.dateSave)
        # 테스트용 출력부
        self.tmpdisplay_label = QLabel(self)
        self.tmpdisplay_label.setGeometry(850, 100, 800, 600)  # 시작x, 시작y, width, height
        self.tmpdisplay_label.setPixmap(pixmap)
        # QLabel의 가운데 정렬 설정
        self.tmpdisplay_label.setAlignment(Qt.AlignCenter)

        # 체크박스 상태 저장 리스트
        self.option_check = [False, False, False]
        # Fall Detection 체크박스
        self.check_fall = QCheckBox("Fall Detection", self)
        self.check_fall.setGeometry(25, 720, 210, 30)  # 위치 및 크기
        self.check_fall.stateChanged.connect(lambda: self.updateOptionCheck(0, self.check_fall.isChecked()))
        # Help Detection 체크박스
        self.check_help = QCheckBox("Help Detection", self)
        self.check_help.setGeometry(25, 770, 210, 30)  # 위치 및 크기
        self.check_help.stateChanged.connect(lambda: self.updateOptionCheck(1, self.check_help.isChecked()))
        # Fire Detection 체크박스
        self.check_fire = QCheckBox("Fire Detection", self)
        self.check_fire.setGeometry(25, 820, 210, 30)  # 위치 및 크기
        self.check_fire.stateChanged.connect(lambda: self.updateOptionCheck(2, self.check_fire.isChecked()))

        # 체크박스 상태 저장 리스트
        self.option_checkv = [False, False, False]
        # Fall Detection 체크박스
        self.check_fallv = QCheckBox("Fall Detection", self)
        self.check_fallv.setGeometry(850, 720, 210, 30)  # 위치 및 크기
        self.check_fallv.stateChanged.connect(lambda: self.updateOptionCheckv(0, self.check_fallv.isChecked()))
        # Help Detection 체크박스
        self.check_helpv = QCheckBox("Help Detection", self)
        self.check_helpv.setGeometry(850, 770, 210, 30)  # 위치 및 크기
        self.check_helpv.stateChanged.connect(lambda: self.updateOptionCheckv(1, self.check_helpv.isChecked()))
        # Fire Detection 체크박스
        self.check_firev = QCheckBox("Fire Detection", self)
        self.check_firev.setGeometry(850, 820, 210, 30)  # 위치 및 크기
        self.check_firev.stateChanged.connect(lambda: self.updateOptionCheckv(2, self.check_firev.isChecked()))

        # QLabel 생성 및 초기 설정
        self.cameralert_label = QLabel("Normal", self)
        self.cameralert_label.setGeometry(500, 720, 240, 80)  # 위치와 사이즈 설정
        self.cameralert_label.setStyleSheet("""
            background-color: white;
            color: green;
            font-size: 30px;
            font-weight: bold;
            text-align: center;
        """)
        self.cameralert_label.setAlignment(Qt.AlignCenter)  # 텍스트 중앙 정렬

        # QLabel 생성 및 초기 설정
        self.cameralert_labelv = QLabel("Normal", self)
        self.cameralert_labelv.setGeometry(1350, 720, 240, 80)  # 위치와 사이즈 설정
        self.cameralert_labelv.setStyleSheet("""
            background-color: white;
            color: green;
            font-size: 30px;
            font-weight: bold;
            text-align: center;
        """)
        self.cameralert_labelv.setAlignment(Qt.AlignCenter)  # 텍스트 중앙 정렬

    def updateOptionCheck(self, index, state):
        """
        업데이트된 체크박스 상태를 리스트에 반영합니다.
        index: self.option_check의 인덱스 (0: Fall, 1: Help, 2: Fire)
        state: 체크 여부 (True / False)
        """
        self.option_check[index] = state
        print(f"Camera Option {index} updated: {self.option_check}")

    def updateOptionCheckv(self, index, state):
        """
        업데이트된 체크박스 상태를 리스트에 반영합니다.
        index: self.option_check의 인덱스 (0: Fall, 1: Help, 2: Fire)
        state: 체크 여부 (True / False)
        """
        self.option_checkv[index] = state
        print(f"Video Option {index} updated: {self.option_checkv}")

    def updateDate(self):
        # time 모듈을 사용해 현재 시간 가져오기
        system_time = time.localtime()  # 현재 로컬 시간 반환
        # 날짜 문자열로 설정
        system_date = f"{system_time.tm_year}-{system_time.tm_mon:02d}-{system_time.tm_mday:02d} {system_time.tm_hour:02d}:{system_time.tm_min:02d}:{system_time.tm_sec:02d}"
        self.date_label.setText(f"Date : {system_date}")
        return system_date
    
    def dateSave(self):
        # 날짜 받아와서 저장하기 버튼
        saved_date = self.updateDate()
        print(saved_date)
        _, sample_img = self.cap.read()
        if self.option_check[0]: 
            sample_img, cropf, is_fall = self.isacfall.fallDetect(sample_img)
        if self.option_check[2]:
            sample_img, is_fire = self.isacfire.fireDetect(sample_img)
            print(is_fire)
        sample_img = cv2.resize(sample_img, (800, 600))
        sample_img = cv2.cvtColor(sample_img, cv2.COLOR_BGR2RGB)
        # numpy 배열을 QImage로 변환
        h, w, ch = sample_img.shape # 프레임 h, w, 채널
        bytes_per_line = ch * w
        qimg = QImage(sample_img.data, w, h, bytes_per_line, QImage.Format_RGB888)
        # QImage를 QPixmap으로 변환 후 QLabel에 설정
        pixmap = QPixmap.fromImage(qimg)
        # QLabel에 이미지 출력
        self.tmpdisplay_label.setPixmap(pixmap)
        self.tmpdisplay_label.repaint()

    # MainWindow 클래스 내에 videoTest 함수 추가
    def videoTest(self):
        # 파일 오픈 다이얼로그를 띄워 비디오 파일 선택
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Video File", "", "Video Files (*.mp4 *.avi *.mov *.mkv)")
        if not file_path:  # 파일이 선택되지 않으면 함수 종료
            print("No file selected.")
            return
        
        # 비디오 캡처 객체 생성
        self.cap = cv2.VideoCapture(file_path)
        if not self.cap.isOpened():
            print(f"Cannot open the video file: {file_path}")
            return
        
        global is_cam_connect
        is_cam_connect = True  # 비디오가 연결된 상태로 설정

        # 프레임 업데이트 타이머 설정
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_video_frame)  # 프레임 업데이트 호출
        self.timer.start(30)  # 30ms마다 호출 (약 33fps)

    def update_video_frame(self):
        # VideoCapture로부터 프레임을 가져옴
        ret, frame = self.cap.read()
        if ret:
            # TODO 여기서 영상처리 함수를 호출하여 사용
            if self.option_checkv[0]: 
                frame, cropf, is_fall = self.isacfall.fallDetect(frame)
            if self.option_checkv[1]:
                is_help = self.isachelp.helpDetect(frame)
                print(is_help)
                self.update_alert_label_helpv(is_help)
            if self.option_checkv[2]:
                frame, is_fire = self.isacfire.fireDetect(frame)
                print(is_fire)
                self.update_alert_label_firev(is_fire)
            # TODO 영상처리 종료

            frame = cv2.resize(frame, (800, 600))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # 이미지를 RGB 형식으로 변환
            h, w, ch = frame.shape  # 프레임의 높이, 너비, 채널 정보
            bytes_per_line = ch * w
            qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimg)
            self.tmpdisplay_label.setPixmap(pixmap)  # QLabel에 이미지 출력
            self.tmpdisplay_label.repaint()  # 즉시 갱신
        else:
            print("Video playback completed.")
            self.timer.stop()  # 타이머 정지
            self.cap.release()  # 비디오 캡처 객체 해제
            global is_cam_connect
            is_cam_connect = False

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
    
    def update_alert_label_fire(self, is_fire):
        if is_fire:
            # 화재 상태
            self.cameralert_label.setText("Fire!!")
            self.cameralert_label.setStyleSheet("""
                background-color: red;
                color: black;
                font-size: 40px;
                font-weight: bold;
                text-align: center;
            """)
        else:
            # 정상 상태
            self.cameralert_label.setText("Normal")
            self.cameralert_label.setStyleSheet("""
                background-color: white;
                color: green;
                font-size: 30px;
                font-weight: bold;
                text-align: center;
            """)
    def update_alert_label_help(self, status_list):
        # 리스트에 True가 있는지 검사
        is_help = any(status for _, status in status_list)
        if is_help:
            # HELP 상태: 노란색 배경, 검정색 글씨
            self.cameralert_label.setText("HELP!")
            self.cameralert_label.setStyleSheet("""
                background-color: yellow;
                color: black;
                font-size: 40px;
                font-weight: bold;
                text-align: center;
            """)
        else:
            # 원래 상태 (Normal)
            self.cameralert_label.setText("Normal")
            self.cameralert_label.setStyleSheet("""
                background-color: white;
                color: green;
                font-size: 30px;
                font-weight: bold;
                text-align: center;
            """)
    def update_alert_label_firev(self, is_fire):
        if is_fire:
            # 화재 상태
            self.cameralert_labelv.setText("Fire!!")
            self.cameralert_labelv.setStyleSheet("""
                background-color: red;
                color: black;
                font-size: 40px;
                font-weight: bold;
                text-align: center;
            """)
        else:
            # 정상 상태
            self.cameralert_labelv.setText("Normal")
            self.cameralert_labelv.setStyleSheet("""
                background-color: white;
                color: green;
                font-size: 30px;
                font-weight: bold;
                text-align: center;
            """)
    def update_alert_label_helpv(self, status_list):
        # 리스트에 True가 있는지 검사
        is_help = any(status for _, status in status_list)
        if is_help:
            # HELP 상태: 노란색 배경, 검정색 글씨
            self.cameralert_labelv.setText("HELP!")
            self.cameralert_labelv.setStyleSheet("""
                background-color: yellow;
                color: black;
                font-size: 40px;
                font-weight: bold;
                text-align: center;
            """)
        else:
            # 원래 상태 (Normal)
            self.cameralert_labelv.setText("Normal")
            self.cameralert_labelv.setStyleSheet("""
                background-color: white;
                color: green;
                font-size: 30px;
                font-weight: bold;
                text-align: center;
            """)


    def update_frame(self):
        # VideoCapture로부터 프레임을 가져옴
        ret, frame = self.cap.read()

        if ret:
            # TODO 여기서 영상처리 함수를 호출하여 사용
            if self.option_check[0]: 
                frame, cropf, is_fall = self.isacfall.fallDetect(frame)
            if self.option_check[1]:
                is_help = self.isachelp.helpDetect(frame)
                print(is_help)
                self.update_alert_label_help(is_help)
            if self.option_check[2]:
                frame, is_fire = self.isacfire.fireDetect(frame)
                print(is_fire)
                self.update_alert_label_fire(is_fire)
            # TODO 영상처리 종료

            # 이미지 출력 시작
            # 이미지를 RGB 형식으로 변환
            frame = cv2.resize(frame, (800, 600))
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
