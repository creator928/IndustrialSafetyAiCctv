# PyQt5 및 OpenCV 라이브러리 임포트
import cv2
import numpy as np
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QFileDialog, QCheckBox, QLineEdit, QTextEdit
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QTimer
import time  # 시간 측정용 라이브러리

# ISAC 패키지 내 탐지 모듈 임포트
from isac_pkg.fallDetector.fallDector import ISAC_FallDetector
from isac_pkg.helpDetector.helpDetector import ISAC_HelpDetector
from isac_pkg.fireDetector.fireDetector import ISAC_FireDetector

# MainWindow 클래스 정의
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # 탐지 모듈 초기화
        self.isacfall_a = ISAC_FallDetector()
        self.isachelp_a = ISAC_HelpDetector()
        self.isacfire_a = ISAC_FireDetector()
        self.isacfall_b = ISAC_FallDetector()
        self.isachelp_b = ISAC_HelpDetector()
        self.isacfire_b = ISAC_FireDetector()

        # 비디오 캡처 객체 초기화
        self.cap_a = None
        self.cap_b = None

        # QTimer 초기화 (비디오 A, B용)
        self.timer_a = QTimer(self)
        self.timer_b = QTimer(self)

        # 체크박스 상태 관리 리스트 (각 비디오의 Fall, Help, Fire 상태 저장)
        self.check_list_a = [False, False, False]
        self.check_list_b = [False, False, False]

        # UI 초기화
        self.initUI()

    def initUI(self):
        # 메인 윈도우 설정
        self.setWindowTitle("ISAC - Industrial Safety A.I CCTV")
        self.setGeometry(100, 100, 2500, 1200)

        # 비디오 A 화면 출력용 QLabel
        self.display_label_a = QLabel(self)
        self.display_label_a.setGeometry(25, 100, 800, 600)
        blank_image = QImage(800, 600, QImage.Format_RGB32)
        blank_image.fill(Qt.black)
        pixmap = QPixmap.fromImage(blank_image)
        self.display_label_a.setPixmap(pixmap)
        self.display_label_a.setAlignment(Qt.AlignCenter)

        # 비디오 A 오픈 버튼
        self.video_button_a = QPushButton("카메라/영상 A", self)
        self.video_button_a.setGeometry(25, 25, 200, 50)
        self.video_button_a.clicked.connect(lambda: self.openVideo("a"))

        # 비디오 A 탐지 기능 체크박스와 경고 레이블
        self.check_fall_a = QCheckBox("낙상감지 A", self)
        self.check_fall_a.setGeometry(25, 720, 250, 30)
        self.check_fall_a.stateChanged.connect(lambda: self.updateCheckList("a", 0, self.check_fall_a.isChecked()))

        self.alert_label_fall_a = QLabel("NORMAL", self)
        self.alert_label_fall_a.setGeometry(330, 720, 150, 40)
        self.initAlertLabel(self.alert_label_fall_a)

        self.check_help_a = QCheckBox("구조감지 A", self)
        self.check_help_a.setGeometry(25, 770, 250, 30)
        self.check_help_a.stateChanged.connect(lambda: self.updateCheckList("a", 1, self.check_help_a.isChecked()))

        self.alert_label_help_a = QLabel("NORMAL", self)
        self.alert_label_help_a.setGeometry(330, 770, 150, 40)
        self.initAlertLabel(self.alert_label_help_a)

        self.check_fire_a = QCheckBox("화재감지 A", self)
        self.check_fire_a.setGeometry(25, 820, 250, 30)
        self.check_fire_a.stateChanged.connect(lambda: self.updateCheckList("a", 2, self.check_fire_a.isChecked()))

        self.alert_label_fire_a = QLabel("NORMAL", self)
        self.alert_label_fire_a.setGeometry(330, 820, 150, 40)
        self.initAlertLabel(self.alert_label_fire_a)

        # 비디오 B 화면 출력용 QLabel
        self.display_label_b = QLabel(self)
        self.display_label_b.setGeometry(900, 100, 800, 600)
        self.display_label_b.setPixmap(pixmap)
        self.display_label_b.setAlignment(Qt.AlignCenter)

        # 비디오 B 오픈 버튼
        self.video_button_b = QPushButton("카메라/영상 B", self)
        self.video_button_b.setGeometry(900, 25, 200, 50)
        self.video_button_b.clicked.connect(lambda: self.openVideo("b"))

        # 비디오 B 탐지 기능 체크박스와 경고 레이블
        self.check_fall_b = QCheckBox("낙상감지 B", self)
        self.check_fall_b.setGeometry(900, 720, 250, 30)
        self.check_fall_b.stateChanged.connect(lambda: self.updateCheckList("b", 0, self.check_fall_b.isChecked()))

        self.alert_label_fall_b = QLabel("NORMAL", self)
        self.alert_label_fall_b.setGeometry(1205, 720, 150, 40)
        self.initAlertLabel(self.alert_label_fall_b)

        self.check_help_b = QCheckBox("구조감지 B", self)
        self.check_help_b.setGeometry(900, 770, 250, 30)
        self.check_help_b.stateChanged.connect(lambda: self.updateCheckList("b", 1, self.check_help_b.isChecked()))

        self.alert_label_help_b = QLabel("NORMAL", self)
        self.alert_label_help_b.setGeometry(1205, 770, 150, 40)
        self.initAlertLabel(self.alert_label_help_b)

        self.check_fire_b = QCheckBox("화재감지 B", self)
        self.check_fire_b.setGeometry(900, 820, 250, 30)
        self.check_fire_b.stateChanged.connect(lambda: self.updateCheckList("b", 2, self.check_fire_b.isChecked()))

        self.alert_label_fire_b = QLabel("NORMAL", self)
        self.alert_label_fire_b.setGeometry(1205, 820, 150, 40)
        self.initAlertLabel(self.alert_label_fire_b)

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

        self.initDataSheet("a")  # 비디오 A용 데이터 시트 생성
        self.initDataSheet("b")  # 비디오 B용 데이터 시트 생성

        self.initEventLogBox() # 이벤트 로그 리스트

        # 비디오 B 오픈 버튼
        self.test_button = QPushButton("Test", self)
        self.test_button.setGeometry(2000, 1050, 250, 70)
        self.test_button.clicked.connect(lambda: self.doTest())

    def doTest(self):
        sample_dict = {"이름":"홍길동","헬멧 색상":"파란색","나이":30,"혈액형":"A","지병 유무":"없음"}
        self.modifyDataSheet(set="a", num=0, dictionary=sample_dict, stat="정상")
        self.appendEventLog("Fire detected in camera A")
        pass

    def updateDate(self):
        # time 모듈을 사용해 현재 시간 가져오기
        system_time = time.localtime()  # 현재 로컬 시간 반환
        # 날짜 문자열로 설정
        system_date = f"{system_time.tm_year}-{system_time.tm_mon:02d}-{system_time.tm_mday:02d} {system_time.tm_hour:02d}:{system_time.tm_min:02d}:{system_time.tm_sec:02d}"
        self.date_label.setText(f"Date : {system_date}")
        return system_date
    
    def updateCheckList(self, label, index, state):
        """
        체크박스 상태 업데이트
        """
        if label == "a":
            self.check_list_a[index] = state
        elif label == "b":
            self.check_list_b[index] = state

    def initAlertLabel(self, label):
        """
        초기 경고 레이블 스타일 설정
        """
        label.setStyleSheet("background-color: white; color: green; font-size: 25px; font-weight: bold;")
        label.setAlignment(Qt.AlignCenter)

    def updateAlertLabels(self, set, fall, help, fire):
        """
        경고 레이블 상태를 업데이트
        """
        if set == "a":
            self.setAlertLabel(self.alert_label_fall_a, fall, "FALL!", "yellow", "black")
            self.setAlertLabel(self.alert_label_help_a, help, "HELP!", "orange", "black")
            self.setAlertLabel(self.alert_label_fire_a, fire, "FIRE!!", "red", "white")
        elif set == "b":
            self.setAlertLabel(self.alert_label_fall_b, fall, "FALL!", "yellow", "black")
            self.setAlertLabel(self.alert_label_help_b, help, "HELP!", "orange", "black")
            self.setAlertLabel(self.alert_label_fire_b, fire, "FIRE!!", "red", "white")

    def setAlertLabel(self, label, condition, text, bg_color, text_color):
        """
        단일 경고 레이블의 상태를 설정
        """
        if condition:
            label.setText(text)
            label.setStyleSheet(f"background-color: {bg_color}; color: {text_color}; font-size: 25px; font-weight: bold;")
        else:
            label.setText("NORMAL")
            label.setStyleSheet("background-color: white; color: green; font-size: 25px; font-weight: bold;")

    def openVideo(self, label):
        """
        비디오 파일 열기 및 타이머 설정
        """
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Video File", "", "Video Files (*.mp4 *.avi *.mov *.mkv)")
        if not file_path:
            return

        if label == "a":
            if self.cap_a:
                self.cap_a.release()
            self.cap_a = cv2.VideoCapture(file_path)
            self.timer_a.timeout.connect(self.updateFrameA)
            self.timer_a.start(30)
        elif label == "b":
            if self.cap_b:
                self.cap_b.release()
            self.cap_b = cv2.VideoCapture(file_path)
            self.timer_b.timeout.connect(self.updateFrameB)
            self.timer_b.start(30)

    def updateFrameA(self):
        """
        비디오 A 프레임 업데이트 및 탐지 모듈 호출
        """
        is_fall, is_help, is_fire = False, False, False
        if self.cap_a is not None and self.cap_a.isOpened():
            ret, frame = self.cap_a.read()
            if ret:
                if self.check_list_a[0]:
                    frame, cropf, is_falls = self.isacfall_a.fallDetect(frame)
                    is_fall = any(status for _, status in is_falls)

                if self.check_list_a[1]:
                    is_helps = self.isachelp_a.helpDetect(frame)
                    is_help = any(status for _, status in is_helps)

                if self.check_list_a[2]:
                    frame, is_fire = self.isacfire_a.fireDetect(frame)

                self.updateAlertLabels("a", is_fall, is_help, is_fire)
                self.displayFrame(frame, self.display_label_a)
            else:
                self.timer_a.stop()
                self.cap_a.release()

    def updateFrameB(self):
        """
        비디오 B 프레임 업데이트 및 탐지 모듈 호출
        """
        is_fall, is_help, is_fire = False, False, False
        if self.cap_b is not None and self.cap_b.isOpened():
            ret, frame = self.cap_b.read()
            if ret:
                if self.check_list_b[0]:
                    frame, cropf, is_falls = self.isacfall_b.fallDetect(frame)
                    is_fall = any(status for _, status in is_falls)

                if self.check_list_b[1]:
                    is_helps = self.isachelp_b.helpDetect(frame)
                    is_help = any(status for _, status in is_helps)

                if self.check_list_b[2]:
                    frame, is_fire = self.isacfire_b.fireDetect(frame)

                self.updateAlertLabels("b", is_fall, is_help, is_fire)
                self.displayFrame(frame, self.display_label_b)
            else:
                self.timer_b.stop()
                self.cap_b.release()

    def displayFrame(self, frame, label):
        """
        프레임을 QLabel에 표시
        """
        frame = cv2.resize(frame, (800, 600))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        label.setPixmap(pixmap)

    # 데이터 시트 생성 메서드 (칸 폭 하드코딩)
    def initDataSheet(self, set):
        """
        데이터 시트를 초기화하여 디스플레이에 추가합니다.
        set: 'a' 또는 'b', 데이터 시트를 비디오 A 또는 B 아래에 생성
        """
        y_offset = 880 if set == 'a' else 880  # Y 위치 조정
        x_offset = 25 if set == 'a' else 900  # X 위치 조정

        # 데이터 시트의 헤더 생성
        header_labels = ["번호", "이름", "헬멧 색상", "나이", "혈액형", "지병 유무", "현재 상태"]
        column_widths = [60, 100, 150, 60, 100, 180, 180]  # 각 칸의 폭을 하드코딩
        row_height = 35  # 칸의 높이

        if set == 'a':
            self.data_sheet_rows_a = []  # 비디오 A의 데이터 시트 저장
            target_sheet = self.data_sheet_rows_a
        elif set == 'b':
            self.data_sheet_rows_b = []  # 비디오 B의 데이터 시트 저장
            target_sheet = self.data_sheet_rows_b
        else:
            raise ValueError("Invalid set identifier. Use 'a' or 'b'.")

        current_x = x_offset  # 현재 X 위치를 추적
        for i, header in enumerate(header_labels):
            header_label = QLabel(header, self)
            header_label.setGeometry(current_x, y_offset, column_widths[i], row_height)
            header_label.setStyleSheet("background-color: lightgray; font-size: 25px; font-weight: bold; text-align: center;")
            header_label.setAlignment(Qt.AlignCenter)
            current_x += column_widths[i]  # 다음 칸의 시작 위치로 이동

        # 데이터 시트의 각 행 생성 (최대 5명)
        for row_idx in range(5):  # 최대 5명
            row_data = []
            current_x = x_offset  # 각 행의 X 위치 초기화
            for col_idx in range(len(header_labels)):
                data_field = QLineEdit(self)
                data_field.setGeometry(current_x, y_offset + row_height + row_idx * row_height, column_widths[col_idx], row_height)
                data_field.setStyleSheet("background-color: white; border: 1px solid lightgray; font-size: 25px;")
                data_field.setAlignment(Qt.AlignCenter)
                data_field.setReadOnly(True)  # 기본적으로 읽기 전용
                row_data.append(data_field)
                current_x += column_widths[col_idx]  # 다음 칸의 시작 위치로 이동
            target_sheet.append(row_data)

        # 가로선 추가
        for row_idx in range(6):  # 5행 + 마지막 구분선
            separator_line = QLabel(self)
            separator_line.setGeometry(x_offset, y_offset + row_height + row_idx * row_height, sum(column_widths), 1)
            separator_line.setStyleSheet("background-color: lightgray;")

    def modifyDataSheet(self, set: str, num: int, dictionary: dict, stat: str):
        """
        데이터 시트의 특정 행에 데이터를 입력하고 상태를 업데이트합니다.
        """
        # 데이터 시트 선택
        if set == "a":
            target_sheet = self.data_sheet_rows_a
        elif set == "b":
            target_sheet = self.data_sheet_rows_b
        else:
            raise ValueError("Invalid set identifier. Use 'a' or 'b'.")

        # 행 번호 유효성 검사
        if num < 0 or num >= len(target_sheet):
            raise IndexError(f"Invalid row number {num}. Must be between 0 and {len(target_sheet) - 1}.")

        # 딕셔너리 키 순서와 데이터 시트 열 순서를 맞추기 위한 키 리스트
        keys = ["이름", "헬멧 색상", "나이", "혈액형", "지병 유무"]

        # 첫 번째 열에 숫자 입력
        target_sheet[num][0].setText(str(num + 1))  # 첫 번째 열에 번호 입력 (1부터 시작)

        # 딕셔너리 데이터 입력
        for col_idx, key in enumerate(keys, start=1):  # 1번부터 데이터 열 시작
            if key in dictionary:
                target_sheet[num][col_idx].setText(str(dictionary[key]))
            else:
                target_sheet[num][col_idx].setText("")  # 키가 없으면 빈 값 설정

        # 상태 열에 상태 문자열 입력
        target_sheet[num][len(keys) + 1].setText(stat)  # 마지막 열에 상태 입력


    # 이벤트 기록 박스 생성 메서드
    def initEventLogBox(self):
        """
        감시 카메라 이벤트를 기록하기 위한 세로로 긴 텍스트 박스를 생성합니다.
        """
        x_offset = 1800  # 이벤트 박스 시작 위치 (오른쪽 공백)
        y_offset = 100   # 박스의 Y 시작 위치
        width = 650      # 박스의 너비
        height = 900     # 박스의 높이

        # QLabel로 제목 생성
        self.event_log_title = QLabel("이벤트 로그", self)
        self.event_log_title.setGeometry(x_offset, y_offset - 50, width, 40)
        self.event_log_title.setStyleSheet("background-color: lightgray; color: black; font-size: 25px; font-weight: bold; text-align: center;")
        self.event_log_title.setAlignment(Qt.AlignCenter)

        # QTextEdit 생성 (이벤트 기록용)
        self.event_log_box = QTextEdit(self)
        self.event_log_box.setGeometry(x_offset, y_offset, width, height)
        self.event_log_box.setStyleSheet("background-color: white; border: 1px solid gray; font-size: 25px;")
        self.event_log_box.setReadOnly(True)  # 읽기 전용으로 설정

    def appendEventLog(self, message):
        """
        이벤트 박스에 새로운 메시지를 추가합니다.
        :param message: 기록할 이벤트 메시지 (문자열)
        """
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())  # 현재 시간 기록
        self.event_log_box.append(f"[{timestamp}] {message}")  # 시간과 메시지 형식으로 추가


    def closeEvent(self, event):
        """
        창 닫을 때 자원 해제
        """
        if self.cap_a:
            self.cap_a.release()
        if self.cap_b:
            self.cap_b.release()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
