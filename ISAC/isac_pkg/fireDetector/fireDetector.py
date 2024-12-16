import cv2
import numpy as np
from ultralytics import YOLO
import cvzone
import time

class FireDetector:
    def __init__(self, model_path="fire.pt", confidence_threshold=0.53):
        # YOLO 모델 초기화
        self.model = YOLO(model_path)
        self.names = self.model.model.names
        self.confidence_threshold = confidence_threshold
        
        # 화재 감지 관련 변수 초기화
        self.first_time = time.time()
        self.maintime = None
        self.count = 0
        self.fire_state = False  # 화재 상태
        self.fire_reset_time = None  # 화재 상태 초기화 시간
        
    def initialize_camera(self, camera_id=0):
        """카메라 초기화"""
        self.cap = cv2.VideoCapture(camera_id)
        return self.cap.isOpened()
    
    def process_frame(self, frame):
        """단일 프레임 처리"""
        frame = cv2.resize(frame, (1024, 768))
        now_time = time.time()
        
        results = self.model.track(frame, verbose=False, persist=True)
        
        if results[0].boxes is not None and results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.int().cpu().tolist()
            class_ids = results[0].boxes.cls.int().cpu().tolist()
            track_ids = results[0].boxes.id.int().cpu().tolist()
            confidences = results[0].boxes.conf.cpu().tolist()
            
            if now_time - self.first_time >= 0.2:
                self.first_time = time.time()
                
                for box, class_id, track_id, conf in zip(boxes, class_ids, track_ids, confidences):
                    if conf >= self.confidence_threshold:
                        if self.count == 0:
                            self.maintime = time.time()
                            self.count += 1
                        else:
                            self.count += 1
                        
                        # 바운딩 박스 및 정보 표시
                        self._draw_detection(frame, box, class_id, track_id, conf)
            
            # 화재 감지 로직
            if self.maintime is not None:
                if now_time - self.maintime >= 3:
                    if self.count >= 10:
                        self.fire_state = True
                        self.fire_reset_time = time.time()  # 마지막 화재 감지 시간 기록
                    self.count = 0
                    self.maintime = None
        
        # 화재 상태 초기화 논리
        if self.fire_reset_time is not None:
            if now_time - self.fire_reset_time > 5:  # 5초 동안 새로운 화재 감지 없으면 초기화
                self.fire_state = False
                self.fire_reset_time = None
        
        return frame, self.fire_state
    
    def _draw_detection(self, frame, box, class_id, track_id, conf):
        """감지된 객체 시각화"""
        x1, y1, x2, y2 = box
        c = self.names[class_id]
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cvzone.putTextRect(frame, f'{track_id}', (x1, y2), 1, 1)
        fconf = conf * 100
        cvzone.putTextRect(frame, f'{c} ({fconf:.2f})', (x1, y1), 1, 1)
    
    def release(self):
        """리소스 해제"""
        if hasattr(self, 'cap'):
            self.cap.release()

def main():
    detector = FireDetector()
    detector.initialize_camera()

    while True:
        ret, frame = detector.cap.read()
        if not ret:
            break
            
        processed_frame, fire_detected = detector.process_frame(frame)
        
        if fire_detected:
            print("Fire Detected!")
            # 화재 경보 로직 추가
        
        cv2.imshow("Fire Detection", processed_frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    detector.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
