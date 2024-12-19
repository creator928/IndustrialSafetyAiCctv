# PyQt5 및 OpenCV 라이브러리 임포트
import cv2
import numpy as np
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QFileDialog, QCheckBox, QLineEdit, QTextEdit, QMessageBox
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QTimer
import time  # 시간 측정용 라이브러리
import os
# ISAC 패키지 내 탐지 모듈 임포트
from isac_pkg.fallDetector.fallDector import ISAC_FallDetector
from isac_pkg.helpDetector.helpDetector import ISAC_HelpDetector
from isac_pkg.fireDetector.fireDetector import ISAC_FireDetector
from isac_pkg.fextDetector.fextDetector import ISAC_FextDetector
from isac_pkg.plcControl.plcControl import ISAC_PLCController

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # 상태 지속성을 위한 변수 초기화
        self.frame_counter_a = 0  # A 카메라의 현재 프레임 넘버
        self.frame_counter_b = 0  # B 카메라의 현재 프레임 넘버
        # 상태 지속성을 위한 변수 초기화 (A와 B로 분리)
        self.event_timestamps_a = {
            "fall": {"last_true_frame": -1, "current_state": False},
            "help": {"last_true_frame": -1, "current_state": False},
            "fire": {"last_true_frame": -1, "current_state": False},
        }

        self.event_timestamps_b = {
            "fall": {"last_true_frame": -1, "current_state": False},
            "help": {"last_true_frame": -1, "current_state": False},
            "fire": {"last_true_frame": -1, "current_state": False},
        }

        # 탐지 모듈 초기화
        self.isacfall_a = ISAC_FallDetector()
        self.isachelp_a = ISAC_HelpDetector()
        self.isacfire_a = ISAC_FireDetector()
        self.isacfext_a = ISAC_FextDetector()

        self.isacfall_b = ISAC_FallDetector()
        self.isachelp_b = ISAC_HelpDetector()
        self.isacfire_b = ISAC_FireDetector()
        self.isacfext_b = ISAC_FextDetector()

        # 비디오 캡처 객체 초기화
        self.cap_a = None
        self.cap_b = None

        # QTimer 초기화 (비디오 A, B용)
        self.timer_a = QTimer(self)
        self.timer_b = QTimer(self)

        # 체크박스 상태 관리 리스트 (각 비디오의 Fall, Help, Fire 상태 저장)
        self.check_list_a = [False, False, False, False]
        self.check_list_b = [False, False, False, False]

        # 로그 스위치 리스트 선언
        self.log_switch_a = [False, False, False]  # 비디오 A용
        self.log_switch_b = [False, False, False]  # 비디오 B용
        self.event_timers_a = [0, 0, 0]  # Fall, Help, Fire 이벤트 상태 변경 시간 (비디오 A용)
        self.event_timers_b = [0, 0, 0]  # Fall, Help, Fire 이벤트 상태 변경 시간 (비디오 B용)

        # 스프링클러 상태 변수
        self.sprinkler_state_a = False  # False: 작동 안 함, True: 작동 중
        self.sprinkler_state_b = False
        
        # PLC 컨트롤러 화재 경고창 온오프 전달값
        self.fire_onoff_a = False
        self.fire_onoff_b = False
        self.plc_onoff = None

        # UI 초기화
        self.initUI()

        # TODO 외부 PLC 접속
        self.plc_controller = ISAC_PLCController('192.168.0.70', 0, 1, 1)
    # region 윈도우 UI 그리기
    def initUI(self):
        window_width = self.width()
        window_height = self.height()
        # 초기 윈도우 설정
        self.setWindowTitle("ISAC - Industrial Safety A.I CCTV")
        self.setGeometry(100, 100, 1600, 900)  # 초기 창 크기

        # 비디오 A 화면 출력용 QLabel
        self.display_label_a = QLabel(self)
        self.display_label_a.setAlignment(Qt.AlignCenter)
        self.display_label_a.setStyleSheet("background-color: black;")

        # 비디오 A 오픈 버튼
        self.video_button_a = QPushButton("영상 A", self)
        self.video_button_a.clicked.connect(lambda: self.openVideo("a"))

        # "카메라 A" 버튼 추가
        self.camera_button_a = QPushButton("카메라 A", self)
        self.camera_button_a.clicked.connect(self.openWebcam)


        # A 세트의 체크박스와 경고 레이블
        self.check_fall_a = QCheckBox("낙상감지 A", self)
        self.alert_label_fall_a = QLabel("NORMAL", self)
        self.alert_label_fall_a.setAlignment(Qt.AlignCenter)
        self.check_fall_a.stateChanged.connect(lambda: self.updateCheckList("a", 0, self.check_fall_a.isChecked()))
        self.initAlertLabel(self.alert_label_fall_a)

        self.check_help_a = QCheckBox("구조감지 A", self)
        self.alert_label_help_a = QLabel("NORMAL", self)
        self.alert_label_help_a.setAlignment(Qt.AlignCenter)
        self.check_help_a.stateChanged.connect(lambda: self.updateCheckList("a", 1, self.check_help_a.isChecked()))
        self.initAlertLabel(self.alert_label_help_a)

        self.check_fire_a = QCheckBox("화재감지 A", self)
        self.alert_label_fire_a = QLabel("NORMAL", self)
        self.alert_label_fire_a.setAlignment(Qt.AlignCenter)
        self.check_fire_a.stateChanged.connect(lambda: self.updateCheckList("a", 2, self.check_fire_a.isChecked()))
        self.initAlertLabel(self.alert_label_fire_a)

        self.check_gear_a = QCheckBox("안전장비감지 A", self)
        self.alert_label_gear_a = QLabel("NORMAL", self)
        self.alert_label_gear_a.setAlignment(Qt.AlignCenter)

        # A 세트의 스프링클러와 소방장비 버튼
        self.water_button_a = QPushButton("스프링클러 작동", self)
        self.water_button_a.setStyleSheet("background-color: skyblue; font-weight: bold;")
        self.water_button_a.clicked.connect(lambda: self.toggleSprinkler("a"))

        self.fext_button_a = QPushButton("소방장비 점검", self)
        self.fext_button_a.setStyleSheet("background-color: orange; font-weight: bold;")
        self.fext_button_a.clicked.connect(lambda: self.fireExtinguisherCheck("a"))

        # 비디오 B 화면 출력용 QLabel
        self.display_label_b = QLabel(self)
        self.display_label_b.setAlignment(Qt.AlignCenter)
        self.display_label_b.setStyleSheet("background-color: black;")

        # 비디오 B 오픈 버튼
        self.video_button_b = QPushButton("영상 B", self)
        self.video_button_b.clicked.connect(lambda: self.openVideo("b"))

        # B 세트의 체크박스와 경고 레이블
        self.check_fall_b = QCheckBox("낙상감지 B", self)
        self.alert_label_fall_b = QLabel("NORMAL", self)
        self.alert_label_fall_b.setAlignment(Qt.AlignCenter)
        self.check_fall_b.stateChanged.connect(lambda: self.updateCheckList("b", 0, self.check_fall_b.isChecked()))
        self.initAlertLabel(self.alert_label_fall_b)

        self.check_help_b = QCheckBox("구조감지 B", self)
        self.alert_label_help_b = QLabel("NORMAL", self)
        self.alert_label_help_b.setAlignment(Qt.AlignCenter)
        self.check_help_b.stateChanged.connect(lambda: self.updateCheckList("b", 1, self.check_help_b.isChecked()))
        self.initAlertLabel(self.alert_label_help_b)

        self.check_fire_b = QCheckBox("화재감지 B", self)
        self.alert_label_fire_b = QLabel("NORMAL", self)
        self.alert_label_fire_b.setAlignment(Qt.AlignCenter)
        self.check_fire_b.stateChanged.connect(lambda: self.updateCheckList("b", 2, self.check_fire_b.isChecked()))
        self.initAlertLabel(self.alert_label_fire_b)

        self.check_gear_b = QCheckBox("안전장비감지 B", self)
        self.alert_label_gear_b = QLabel("NORMAL", self)
        self.alert_label_gear_b.setAlignment(Qt.AlignCenter)
        self.check_gear_b.stateChanged.connect(lambda: self.updateCheckList("b", 3, self.check_gear_b.isChecked()))


        # B 세트의 스프링클러와 소방장비 버튼
        self.water_button_b = QPushButton("스프링클러 작동", self)
        self.water_button_b.setStyleSheet("background-color: skyblue; font-weight: bold;")
        self.water_button_b.clicked.connect(lambda: self.toggleSprinkler("b"))


        self.fext_button_b = QPushButton("소방장비 점검", self)
        self.fext_button_b.setStyleSheet("background-color: orange; font-weight: bold;")
        self.fext_button_b.clicked.connect(lambda: self.fireExtinguisherCheck("b"))


        # 이벤트 로그 제목 QLabel
        self.event_log_title = QLabel("이벤트 로그", self)
        self.event_log_title.setAlignment(Qt.AlignCenter)
        self.event_log_title.setStyleSheet(f"background-color: lightgray; color: black; font-size: {int(window_height * 0.025)}px; font-weight: bold; text-align: center;")

        # 이벤트 로그 QTextEdit
        self.event_log_box = QTextEdit(self)
        self.event_log_box.setReadOnly(True)  # 읽기 전용 설정
        self.event_log_box.setStyleSheet(f"background-color: white; border: 1px solid gray; font-size: {int(window_height * 0.025)}px;")
        
        # 현재 시간 표시용 QLabel
        self.date_label = QLabel("Date : ", self)
        self.date_label.setAlignment(Qt.AlignLeft)
        self.date_label.setStyleSheet(f"font-size: {int(window_height * 0.025)}px; font-weight: bold; color: black;")

        # 타이머 설정 (1초마다 업데이트)
        self.date_timer = QTimer(self)
        self.date_timer.timeout.connect(self.updateDate)
        self.date_timer.start(1000)  # 1000ms = 1초
        self.updateDate()

        # UI 업데이트
        self.updateUI()
    # endregion 윈도우 UI 그리기 끝

    # region 창 크기 변경 관련 함수
    def resizeEvent(self, event):
        # 창 크기 변경 시 UI 업데이트
        self.updateUI()

    def updateUI(self):
        # 현재 창 크기 가져오기
        window_width = self.width()
        window_height = self.height()

        # 비디오 A 화면 크기 및 위치
        self.display_label_a.setGeometry(int(window_width * 0.025), int(window_height * 0.07), int(window_width * 0.35), int(window_height * 0.45))

        # 비디오 A 오픈 버튼 크기 및 위치
        self.video_button_a.setGeometry(int(window_width * 0.025), int(window_height * 0.02), int(window_width * 0.12), int(window_height * 0.05))
        self.video_button_a.setStyleSheet(f"font-size: {int(window_height * 0.025)}px;")

        # "카메라 A" 버튼 위치 및 크기
        self.camera_button_a.setGeometry(
            self.video_button_a.geometry().right() + int(window_width * 0.01),
            self.video_button_a.geometry().top(),
            int(window_width * 0.12),
            self.video_button_a.height(),
            )
        self.camera_button_a.setStyleSheet(f"font-size: {int(window_height * 0.025)}px;")


        # 체크박스와 경고 레이블 위치 및 크기
        self.check_fall_a.setGeometry(int(window_width * 0.025), int(window_height * 0.525), int(window_width * 0.12), int(window_height * 0.05))
        self.check_fall_a.setStyleSheet(f"font-size: {int(window_height * 0.025)}px;")
        self.alert_label_fall_a.setGeometry(int(window_width * 0.12), int(window_height * 0.525), int(window_width * 0.12), int(window_height * 0.05))
        self.alert_label_fall_a.setStyleSheet(f"font-size: {int(window_height * 0.025)}px;")

        self.check_help_a.setGeometry(int(window_width * 0.025), int(window_height * 0.575), int(window_width * 0.12), int(window_height * 0.05))
        self.check_help_a.setStyleSheet(f"font-size: {int(window_height * 0.025)}px;")
        self.alert_label_help_a.setGeometry(int(window_width * 0.12), int(window_height * 0.575), int(window_width * 0.12), int(window_height * 0.05))
        self.alert_label_help_a.setStyleSheet(f"font-size: {int(window_height * 0.025)}px;")

        self.check_fire_a.setGeometry(int(window_width * 0.025), int(window_height * 0.625), int(window_width * 0.12), int(window_height * 0.05))
        self.check_fire_a.setStyleSheet(f"font-size: {int(window_height * 0.025)}px;")
        self.alert_label_fire_a.setGeometry(int(window_width * 0.12), int(window_height * 0.625), int(window_width * 0.12), int(window_height * 0.05))
        self.alert_label_fire_a.setStyleSheet(f"font-size: {int(window_height * 0.025)}px;")

        self.check_gear_a.setGeometry(int(window_width * 0.025), int(window_height * 0.675), int(window_width * 0.12), int(window_height * 0.05))
        self.check_gear_a.setStyleSheet(f"font-size: {int(window_height * 0.025)}px;")
        self.alert_label_gear_a.setGeometry(int(window_width * 0.12), int(window_height * 0.675), int(window_width * 0.12), int(window_height * 0.05))
        self.alert_label_gear_a.setStyleSheet(f"font-size: {int(window_height * 0.025)}px;")

        # 스프링클러와 소방장비 버튼 위치 및 크기
        self.water_button_a.setGeometry(int(window_width * 0.25), int(window_height * 0.55), int(window_width * 0.12), int(window_height * 0.05))
        self.water_button_a.setStyleSheet(f"background-color: skyblue; font-weight: bold; font-size: {int(window_height * 0.025)}px;")

        self.fext_button_a.setGeometry(int(window_width * 0.25), int(window_height * 0.65), int(window_width * 0.12), int(window_height * 0.05))
        self.fext_button_a.setStyleSheet(f"background-color: orange; font-weight: bold; font-size: {int(window_height * 0.025)}px;")

        # 비디오 B 화면 크기 및 위치
        self.display_label_b.setGeometry(int(window_width * 0.4), int(window_height * 0.07), int(window_width * 0.35), int(window_height * 0.45))

        # 비디오 B 오픈 버튼 크기 및 위치
        self.video_button_b.setGeometry(int(window_width * 0.4), int(window_height * 0.02), int(window_width * 0.12), int(window_height * 0.05))
        self.video_button_b.setStyleSheet(f"font-size: {int(window_height * 0.025)}px;")

        # 체크박스와 경고 레이블 위치 및 크기
        self.check_fall_b.setGeometry(int(window_width * 0.4), int(window_height * 0.525), int(window_width * 0.12), int(window_height * 0.05))
        self.check_fall_b.setStyleSheet(f"font-size: {int(window_height * 0.025)}px;")
        self.alert_label_fall_b.setGeometry(int(window_width * 0.495), int(window_height * 0.525), int(window_width * 0.12), int(window_height * 0.05))
        self.alert_label_fall_b.setStyleSheet(f"font-size: {int(window_height * 0.025)}px;")

        self.check_help_b.setGeometry(int(window_width * 0.4), int(window_height * 0.575), int(window_width * 0.12), int(window_height * 0.05))
        self.check_help_b.setStyleSheet(f"font-size: {int(window_height * 0.025)}px;")
        self.alert_label_help_b.setGeometry(int(window_width * 0.495), int(window_height * 0.575), int(window_width * 0.12), int(window_height * 0.05))
        self.alert_label_help_b.setStyleSheet(f"font-size: {int(window_height * 0.025)}px;")

        self.check_fire_b.setGeometry(int(window_width * 0.4), int(window_height * 0.625), int(window_width * 0.12), int(window_height * 0.05))
        self.check_fire_b.setStyleSheet(f"font-size: {int(window_height * 0.025)}px;")
        self.alert_label_fire_b.setGeometry(int(window_width * 0.495), int(window_height * 0.625), int(window_width * 0.12), int(window_height * 0.05))
        self.alert_label_fire_b.setStyleSheet(f"font-size: {int(window_height * 0.025)}px;")

        self.check_gear_b.setGeometry(int(window_width * 0.4), int(window_height * 0.675), int(window_width * 0.12), int(window_height * 0.05))
        self.check_gear_b.setStyleSheet(f"font-size: {int(window_height * 0.025)}px;")
        self.alert_label_gear_b.setGeometry(int(window_width * 0.495), int(window_height * 0.675), int(window_width * 0.12), int(window_height * 0.05))
        self.alert_label_gear_b.setStyleSheet(f"font-size: {int(window_height * 0.025)}px;")

        # 스프링클러와 소방장비 버튼 위치 및 크기
        self.water_button_b.setGeometry(int(window_width * 0.62), int(window_height * 0.55), int(window_width * 0.12), int(window_height * 0.05))
        self.water_button_b.setStyleSheet(f"background-color: skyblue; font-weight: bold; font-size: {int(window_height * 0.025)}px;")

        self.fext_button_b.setGeometry(int(window_width * 0.62), int(window_height * 0.65), int(window_width * 0.12), int(window_height * 0.05))
        self.fext_button_b.setStyleSheet(f"background-color: orange; font-weight: bold; font-size: {int(window_height * 0.025)}px;")

        # 이벤트 로그 제목 및 박스 위치 및 크기
        event_log_x = int(window_width * 0.775)  # 오른쪽 여유 공간에 위치
        event_log_y = int(window_height * 0.025)  # 위쪽 여백
        event_log_width = int(window_width * 0.2)  # 오른쪽에 차지하는 폭
        event_log_height = int(window_height * 0.9)  # 전체 높이

        # 제목 크기 및 위치
        self.event_log_title.setGeometry(event_log_x, event_log_y, event_log_width, int(window_height * 0.03))
        self.event_log_title.setStyleSheet(f"background-color: lightgray; font-size: {int(window_height * 0.02)}px; font-weight: bold; color: black;")

        # 이벤트 로그 박스 크기 및 위치
        self.event_log_box.setGeometry(event_log_x, event_log_y + int(window_height * 0.035), event_log_width, event_log_height)
        self.event_log_box.setStyleSheet(f"font-size: {int(window_height * 0.02)}px; background-color: white; border: 1px solid gray;")

        # 현재 시간 표시 QLabel 위치 및 크기
        self.date_label.setGeometry(int(window_width * 0.01), int(window_height * 0.95), int(window_width * 0.4), int(window_height * 0.04))
        self.date_label.setStyleSheet(f"font-size: {int(window_height * 0.03)}px; color: black;")
    # endregion 창 크기 변경 관련 함수 끝

    # 시간 업데이트 함수(좌하단 시계)
    def updateDate(self):
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        self.date_label.setText(f"Date: {current_time}")
        return current_time
    
    # 그냥 테스트용 함수
    def doTest(self):
        sample_dict = {"이름":"홍길동","헬멧 색상":"파란색","나이":30,"혈액형":"A","지병 유무":"없음"}
        self.modifyDataSheet(set="a", num=0, dictionary=sample_dict, stat="정상")
        self.appendEventLog("Fire detected in camera A")
        pass

    # region 체크 박스 및 경고창 관련 함수
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
        window_width = self.width()
        window_height = self.height()
        label.setStyleSheet(f"background-color: white; color: green; font-size: {int(window_height * 0.025)}px; font-weight: bold;")
        label.setAlignment(Qt.AlignCenter)

    def updateAlertLabels(self, set, fall, help, fire):
        """
        경고 레이블 상태를 업데이트
        """
        if set == "a":
            self.setAlertLabel(self.alert_label_fall_a, fall, "FALL!", "yellow", "black", set, 0)
            self.setAlertLabel(self.alert_label_help_a, help, "HELP!", "orange", "black", set, 1)
            self.setAlertLabel(self.alert_label_fire_a, fire, "FIRE!!", "red", "white", set, 2)
        elif set == "b":
            self.setAlertLabel(self.alert_label_fall_b, fall, "FALL!", "yellow", "black", set, 0)
            self.setAlertLabel(self.alert_label_help_b, help, "HELP!", "orange", "black", set, 1)
            self.setAlertLabel(self.alert_label_fire_b, fire, "FIRE!!", "red", "white", set, 2)

    def setAlertLabel(self, label, condition, text, bg_color, text_color, set_name: str, index: int):
        """
        단일 경고 레이블의 상태를 설정하고 이벤트 로그를 기록합니다.
        :param label: 대상 QLabel
        :param condition: 이벤트 감지 여부
        :param text: 경고 메시지 텍스트
        :param bg_color: 경고 메시지 배경색
        :param text_color: 경고 메시지 글자색
        :param set_name: 이벤트 발생 세트 이름 ("a" 또는 "b")
        :param index: 이벤트 인덱스 (Fall: 0, Help: 1, Fire: 2)
        """
        window_width = self.width()
        window_height = self.height()
        if condition:
            label.setText(text)
            label.setStyleSheet(f"background-color: {bg_color}; color: {text_color}; font-size: {int(window_height * 0.025)}px; font-weight: bold;")
        else:
            label.setText("NORMAL")
            label.setStyleSheet(f"background-color: white; color: green; font-size: {int(window_height * 0.025)}px; font-weight: bold;")
        # PLC 컨트롤러 화재 온오프 전달
        if text == "FIRE!!":
                self.plc_onoff = self.fireOnOffCall(set_name, condition)
                if self.plc_onoff is not None:
                    print(self.plc_onoff)
                    # TODO PLC 화재 정보 전달
                    if self.plc_onoff == True:
                        self.plc_controller.controlBit(2, True)
                    elif self.plc_onoff == False: 
                        self.plc_controller.controlBit(2, False)
                    elif self.plc_onoff == None :
                        pass
        
        # 이벤트 로그 관리
        if set_name == "a":
            self.detectedEventLog(condition, text, self.log_switch_a, self.event_timers_a, index, set_name)
        elif set_name == "b":
            self.detectedEventLog(condition, text, self.log_switch_b, self.event_timers_b, index, set_name)
    # PLC 컨트롤러 화재 경고창 온오프 전달
    def fireOnOffCall(self, identifier: str, condition: bool):
        """
        identifier와 condition 값을 받아 상태 변화를 추적하여 알림을 반환합니다.
        
        Args:
            identifier (str): "a" 또는 "b"로 구분되는 대상
            condition (bool): 현재 상태 값
        
        Returns:
            bool or None: 상태 변화에 따른 알림 값
                          - True: 상태가 False에서 True로 변경됨
                          - False: 상태가 True에서 False로 변경됨
                          - None: 상태가 변경되지 않음
        """
        if identifier == "a":
            if condition != self.fire_onoff_a:
                self.fire_onoff_a = condition
                return condition
        elif identifier == "b":
            if condition != self.fire_onoff_b:
                self.fire_onoff_b = condition
                return condition
        return None  # 상태가 변경되지 않음
    def detectedEventLog(self, condition: bool, text: str, logswitch: list, event_timers: list, index: int, set_name: str):
        """
        감지 이벤트를 로그에 출력하고 상태 전환 시 임계 시간을 고려합니다.
        :param condition: 이벤트 감지 여부 (True/False)
        :param text: 이벤트 발생 시 출력할 텍스트
        :param logswitch: 이벤트 스위치 리스트 (log_switch_a 또는 log_switch_b)
        :param event_timers: 이벤트 상태 변경 시간을 관리하는 리스트
        :param index: 이벤트 인덱스 (Fall: 0, Help: 1, Fire: 2)
        :param set_name: 이벤트 발생 세트 이름 ("a" 또는 "b")
        """
        current_time = time.time()  # 현재 시간(초)
        # 상태 변경 감지
        if condition != logswitch[index]:  # 상태가 변경된 경우
            event_timers[index] = current_time  # 상태 변경 시간 기록

        # 상태가 True로 일정 시간 이상 지속된 경우
        if condition and not logswitch[index] and (current_time - event_timers[index] >= 0):  # 2초 지속
            logswitch[index] = True  # 상태 전환
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            self.event_log_box.append(f"[{timestamp}] {text} 상황 발생 ({set_name.upper()} 카메라)")
    
        # 상태가 False로 일정 시간 이상 지속된 경우
        elif not condition and logswitch[index] and (current_time - event_timers[index] >= 0):  # 2초 지속
            logswitch[index] = False  # 상태 전환
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            self.event_log_box.append(f"[{timestamp}] {text} 상황 종료 ({set_name.upper()} 카메라)")
    # endregion 체크 박스 및 경고창 관련 끝

    # region 비디오 핸들링 함수
    def openVideo(self, label):
        """
        비디오 파일 열기 및 타이머 설정
        """
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Video File", "", "Video Files (*.mp4 *.avi *.mov *.mkv)")
        if not file_path:
            return

        # 이전 자원을 안전하게 해제
        if label == "a":
            self.stopWebcam()  # 웹캠 세션 종료
            if self.cap_a:  # 기존 비디오 자원 해제
                self.cap_a.release()
            self.cap_a = cv2.VideoCapture(file_path)
            if not self.cap_a.isOpened():  # 비디오 열기 실패 시
                QMessageBox.critical(self, "Error", "Cannot open the video file.")
                return

            # 기존 타이머 연결 해제 후 새로운 신호 연결
            if self.timer_a.isActive():
                self.timer_a.stop()
            try:
                self.timer_a.timeout.disconnect(self.updateFrameA)  # 안전한 해제
            except TypeError:
                pass  # 이미 연결이 해제된 경우

            self.timer_a.timeout.connect(self.updateFrameA)
            self.timer_a.start(30)
        elif label == "b":
            self.stopWebcam()  # 웹캠 세션 종료
            if self.cap_b:  # 기존 비디오 자원 해제
                self.cap_b.release()
            self.cap_b = cv2.VideoCapture(file_path)
            if not self.cap_b.isOpened():  # 비디오 열기 실패 시
                QMessageBox.critical(self, "Error", "Cannot open the video file.")
                return

            # 기존 타이머 연결 해제 후 새로운 신호 연결
            if self.timer_b.isActive():
                self.timer_b.stop()
            try:
                self.timer_b.timeout.disconnect(self.updateFrameB)  # 안전한 해제
            except TypeError:
                pass  # 이미 연결이 해제된 경우

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
                
                is_fall, is_help, is_fire = self.eventContinuity("a", is_fall, is_help, is_fire)

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

                is_fall, is_help, is_fire = self.eventContinuity("b", is_fall, is_help, is_fire)

                self.updateAlertLabels("b", is_fall, is_help, is_fire)
                self.displayFrame(frame, self.display_label_b)
            else:
                self.timer_b.stop()
                self.cap_b.release()

    def displayFrame(self, frame, label):
        """
        프레임을 QLabel에 표시
        """
        window_width = self.width()
        window_height = self.height()
        frame = cv2.resize(frame, (int(window_width * 0.35), int(window_height * 0.45)))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        label.setPixmap(pixmap)
    # endregion 비디오 핸들링 함수 끝

    # region 이벤트 로그 테스트 및 이벤트 지속성 평가
    def appendEventLog(self, message):
        """
        이벤트 박스에 새로운 메시지를 추가합니다.
        :param message: 기록할 이벤트 메시지 (문자열)
        """
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())  # 현재 시간 기록
        self.event_log_box.append(f"[{timestamp}] {message}")  # 시간과 메시지 형식으로 추가

    def eventContinuity(self, label, is_fall, is_help, is_fire):
        """
        이벤트 상태 지속성을 관리하는 함수.
        특정 상태(True)가 발생한 이후 16 프레임 동안 False 상태가 지속되지 않으면 상태를 유지합니다.

        :param is_fall: 현재 프레임의 낙상 상태
        :param is_help: 현재 프레임의 도움 요청 상태
        :param is_fire: 현재 프레임의 화재 상태
        :param label: "a" 또는 "b"로 카메라를 구분
        :return: 지속된 상태를 고려한 is_fall, is_help, is_fire
        """
        # 카메라에 따라 적절한 상태 변수 선택
        if label == "a":
            event_timestamps = self.event_timestamps_a
            self.frame_counter_a += 1
            current_frame = self.frame_counter_a
        elif label == "b":
            event_timestamps = self.event_timestamps_b
            self.frame_counter_b += 1
            current_frame = self.frame_counter_b
        else:
            raise ValueError("Invalid label. Use 'a' or 'b'.")

        # 이벤트별로 상태 지속성 관리
        results = {}
        for event, is_event in zip(["fall", "help", "fire"], [is_fall, is_help, is_fire]):
            if is_event:  # True 상태가 들어온 경우
                event_timestamps[event]["last_true_frame"] = current_frame  # 마지막 True 프레임 기록
                event_timestamps[event]["current_state"] = True  # 상태 유지
            else:  # False 상태일 경우 지속성 체크
                last_true_frame = event_timestamps[event]["last_true_frame"]
                if current_frame - last_true_frame > 16:  # 16 프레임 이상 False가 지속되면 상태 변경
                    event_timestamps[event]["current_state"] = False

            # 현재 상태 기록
            results[event] = event_timestamps[event]["current_state"]

        return results["fall"], results["help"], results["fire"]
    # endregion 이벤트 로그 테스트 및 이벤트 지속성 평가 끝

    # region 스프링클러 작동 버튼
    def toggleSprinkler(self, label):
        """
        스프링클러 버튼 상태를 토글합니다.
        :param label: "a" 또는 "b"로 비디오 세트를 구분
        """
        window_width = self.width()
        window_height = self.height()
        if label == "a":
            if not self.sprinkler_state_a:  # 스프링클러 작동
                self.water_button_a.setText("스프링클러 정지")
                self.water_button_a.setStyleSheet(f"background-color: darkblue; color: white; font-size: {int(window_height * 0.025)}px; font-weight: bold;")
                self.sprinkler_state_a = True
                # TODO T/F를 받는 함수
                # print(self.sprinkler_state_a)
                if self.sprinkler_state_a == True:
                    self.plc_controller.controlBit(0, True)
                    self.plc_controller.controlBit(0, False) 

            else:  # 스프링클러 정지
                self.water_button_a.setText("스프링클러 작동")
                self.water_button_a.setStyleSheet(f"background-color: skyblue; color: black; font-size: {int(window_height * 0.025)}px; font-weight: bold;")
                self.sprinkler_state_a = False
                # TODO T/F를 받는 함수
                # print(self.sprinkler_state_a)
                if self.sprinkler_state_a == False:
                    self.plc_controller.controlBit(1, True)
                    self.plc_controller.controlBit(1, False) 

        elif label == "b":
            if not self.sprinkler_state_b:  # 스프링클러 작동
                self.water_button_b.setText("스프링클러 정지")
                self.water_button_b.setStyleSheet(f"background-color: darkblue; color: white; font-size: {int(window_height * 0.025)}px; font-weight: bold;")
                self.sprinkler_state_b = True
                # TODO T/F를 받는 함수
                # print(self.sprinkler_state_b)
                if self.sprinkler_state_b == True:
                    self.plc_controller.controlBit(0, True)
                    self.plc_controller.controlBit(0, False) 

            else:  # 스프링클러 정지
                self.water_button_b.setText("스프링클러 작동")
                self.water_button_b.setStyleSheet(f"background-color: skyblue; color: black; font-size: {int(window_height * 0.025)}px; font-weight: bold;")
                self.sprinkler_state_b = False
                # TODO T/F를 받는 함수
                # print(self.sprinkler_state_b)
                if self.sprinkler_state_b == False:
                    self.plc_controller.controlBit(1, True)
                    self.plc_controller.controlBit(1, False) 
    # endregion 스프링클러 작동 버튼 끝

    # region 소화기 탐지 버튼
    def fireExtinguisherCheck(self, set_name):
        """
        소화기 탐지 상태를 확인하고 이벤트 로그에 기록합니다.
        :param set_name: "a" 또는 "b"로 세트를 구분
        """
        try:
            # 프레임 가져오기
            if set_name == "a":
                # A 세트: 웹캠이 연결되어 있으면 웹캠에서, 아니면 비디오에서 프레임을 가져옴
                if hasattr(self, "webcam_cap") and self.webcam_cap.isOpened():
                    ret, frame = self.webcam_cap.read()
                elif self.cap_a and self.cap_a.isOpened():
                    ret, frame = self.cap_a.read()
                else:
                    frame = None
            elif set_name == "b":
                # B 세트: 비디오에서 프레임을 가져옴
                if self.cap_b and self.cap_b.isOpened():
                    ret, frame = self.cap_b.read()
                else:
                    frame = None
            else:
                self.appendEventLog(f"잘못된 카메라 이름: {set_name}")
                return
            # 프레임이 없는 경우
            if frame is None:
                self.appendEventLog(f"{set_name.upper()} 세트: 소화기 탐지 실패 - 현재 프레임이 없습니다.")
                return

            # 세트별로 올바른 탐지 모듈 호출
            if set_name == "a":
                status = self.isacfext_a._detect_fire_ext(frame)
            elif set_name == "b":
                status = self.isacfext_b._detect_fire_ext(frame)
            else:
                self.appendEventLog(f"잘못된 카메라 번호 : {set_name}")
                return

            # 상태에 따라 이벤트 로그에 기록
            if status == True:
                self.appendEventLog(f"{set_name.upper()} 카메라 : 소화기 정상 배치 확인 완료.")
            elif status == False:
                self.appendEventLog(f"{set_name.upper()} 카메라 : 경고! 소화기 배치 이상!")
            else:
                self.appendEventLog(f"{set_name.upper()} 카메라 : 알 수 없는 상태 코드 - {status}")
        except Exception as e:
            self.appendEventLog(f"{set_name.upper()} 카메라 : 소화기 탐지 중 오류 발생 - {str(e)}")
    # endregion 소화기 탐지 버튼

    # region 웹캠 관련 함수
    def openWebcam(self):
        """
        웹캠을 열어 실시간으로 display_label_a에 출력합니다.
        """
        self.stopWebcam()  # 이전 세션 정리
        if self.cap_a:  # 비디오 자원 해제
            self.cap_a.release()
        if self.cap_b:  # 비디오 자원 해제
            self.cap_b.release()
        self.timer_a.stop()  # 기존 타이머 정지
        self.timer_b.stop()  # 기존 타이머 정지

        self.webcam_cap = cv2.VideoCapture(0)  # 웹캠 열기
        if not self.webcam_cap.isOpened():
            QMessageBox.critical(self, "Error", "Cannot access the webcam.")
            return

        self.webcam_timer = QTimer(self)
        self.webcam_timer.timeout.connect(self.updateWebcamA)
        self.webcam_timer.start(33)  # 약 33fps로 업데이트

    def updateWebcamA(self):
        """
        웹캠 프레임을 display_label_a에 실시간으로 표시합니다.
        """
        is_fall, is_help, is_fire = False, False, False
        if self.webcam_cap is not None and self.webcam_cap.isOpened():
            ret, frame = self.webcam_cap.read()
            if ret:
                if self.check_list_a[0]:
                    frame, cropf, is_falls = self.isacfall_a.fallDetect(frame)
                    is_fall = any(status for _, status in is_falls)

                if self.check_list_a[1]:
                    is_helps = self.isachelp_a.helpDetect(frame)
                    is_help = any(status for _, status in is_helps)

                if self.check_list_a[2]:
                    frame, is_fire = self.isacfire_a.fireDetect(frame)

                is_fall, is_help, is_fire = self.eventContinuity("a", is_fall, is_help, is_fire)

                self.updateAlertLabels("a", is_fall, is_help, is_fire)
                self.displayFrame(frame, self.display_label_a)
            else:
                self.stopWebcam()  # 프레임 읽기 실패 시 웹캠 종료

    def stopWebcam(self):
        """
        웹캠 사용을 중지하고 자원을 해제합니다.
        """
        if hasattr(self, "webcam_timer") and self.webcam_timer.isActive():
            self.webcam_timer.stop()  # 타이머 정지
        if hasattr(self, "webcam_cap") and self.webcam_cap.isOpened():
            self.webcam_cap.release()  # 웹캠 해제
    # endregion 웹캠 관련 함수

    def closeEvent(self, event):
        """
        창 닫을 때 자원 해제
        """
        self.stopWebcam()  # 웹캠 먼저 정지
        if self.cap_a:
            self.cap_a.release()  # 비디오 A 해제
        if self.cap_b:
            self.cap_b.release()  # 비디오 B 해제
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
