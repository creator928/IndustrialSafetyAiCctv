import os
import cv2
from ultralytics import YOLO
import cvzone
import time


# 현재 파일 safetyMonitor.py가 위치한 디렉터리 경로 가져오기
current_dir = os.path.dirname(__file__)
# fire_ex.pt 파일의 전체 경로 생성
fire_ext_model_path = os.path.join(current_dir, "fire_ext.pt")

person_model_path = "yolo11s.pt"

class ISAC_FextDetector:
    def __init__(self):
        """
        클래스 초기화: 모델 로드 및 변수 초기화
        Args:
            person_model_path: 사람 감지 YOLO 모델 경로
            fire_ext_model_path: 소화기 감지 YOLO 모델 경로
        """
        global person_model_path
        global fire_ext_model_path
        self.person_model = YOLO(person_model_path)  # 사람 감지 모델
        self.fire_ext_model = YOLO(fire_ext_model_path)  # 소화기 감지 모델

        self.person_class_id = self._find_person_class_id(self.person_model.model.names)

        # 상태 변수 초기화
        self.person_count = 0
        self.fire_ext_count = 0
        self.maintime = time.time()
        self.detecttime = time.time()
        self.emergency = False

    def _find_person_class_id(self, class_names):
        """
        'person' 클래스의 ID를 찾는 내부 함수
        Args:
            class_names: 모델 클래스 이름 딕셔너리
        Returns:
            person_class_id: 'person' 클래스의 ID
        """
        for class_id, class_name in class_names.items():
            if class_name == "person":
                return class_id
        raise ValueError("Error: 'person' 클래스가 모델 클래스 이름에 존재하지 않습니다.")

    def fextDetect(self, frame):    # emergency_status반환 0:안전 1:위험 2:비정상(사람 x)
        """
        입력 프레임에서 사람과 소화기를 감지하고 안전 여부를 판단 (0.2초마다 디텍팅, 5초마다 판단)
        Args:
            frame: 입력 이미지 프레임
        Returns:
            annotated_frame: 결과가 그려진 이미지 프레임
            emergency_status: 안전 상태 (0: 안전, 1: 위험, 2: 비정상 상태)
        """
        # 시간 확인
        nowtime = time.time()

        # 프레임 크기 조정
        frame = cv2.resize(frame, (1020, 600))

        # 0.2초마다 디텍팅
        if nowtime - self.detecttime >= 0.2:
            self.detecttime = time.time()

            # 사람 감지
            person_detected = self._detect_person(frame)

            # 소화기 감지
            fire_ext_detected = self._detect_fire_ext(frame)

            # 감지 결과 카운트 업데이트
            if person_detected and fire_ext_detected:
                self.fire_ext_count += 1
                self.person_count += 1
            elif person_detected:
                self.person_count += 1
            elif fire_ext_detected:
                self.fire_ext_count += 1

        # 5초마다 상태 판단
        emergency_status = None
        if nowtime - self.maintime >= 5:
            self.maintime = time.time()
            if self.person_count >= 5:  # 사람이 1초 이상 감지
                if self.fire_ext_count >= 18:  # 소화기가 3.6초 이상 감지
                    emergency_status = 0  # 안전 상태
                else:
                    emergency_status = 1  # 위험 상태
            else:
                emergency_status = 2  # 비정상 상태

            # 카운터 초기화
            self.person_count = 0
            self.fire_ext_count = 0

        # 결과 반환
        return frame, emergency_status

    def _detect_person(self, frame):
        """사람 감지"""
        results = self.person_model.track(frame, verbose=False, persist=True)
        if results and hasattr(results[0], 'boxes') and results[0].boxes is not None:
            boxes = results[0].boxes.xyxy.int().cpu().tolist()
            class_ids = results[0].boxes.cls.int().cpu().tolist()
            confidences = results[0].boxes.conf.cpu().tolist()

            for box, class_id, conf in zip(boxes, class_ids, confidences):
                if class_id == self.person_class_id and conf >= 0.7:
                    x1, y1, x2, y2 = box
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cvzone.putTextRect(frame, f'Person {conf:.2f}', (x1, y1), 1, 1)
                    return True
        return False

    def _detect_fire_ext(self, frame):
        """소화기 감지"""
        results = self.fire_ext_model.track(frame, verbose=False, persist=True)
        if results and hasattr(results[0], 'boxes') and results[0].boxes is not None:
            boxes = results[0].boxes.xyxy.int().cpu().tolist()
            confidences = results[0].boxes.conf.cpu().tolist()

            for box, conf in zip(boxes, confidences):
                if conf >= 0.7:
                    x1, y1, x2, y2 = box
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cvzone.putTextRect(frame, f'Fire Ext {conf:.2f}', (x1, y1), 1, 1)
                    return True
        return False
