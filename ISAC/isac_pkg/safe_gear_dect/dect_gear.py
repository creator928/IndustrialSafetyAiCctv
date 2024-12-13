import cv2
import numpy as np
from ultralytics import YOLO
import cvzone


"""
best_cls4_200.pt info
class : helmet , no helemt, vest, no vest
epoch : 200
model : yolov11m(task:dection)
"""
# YOLOv11 모델 불러오기
model = YOLO("best_cls4_200.pt")  # 학습된 YOLO 모델 로드
names = model.model.names  # 클래스 이름 불러오기

# 비디오 파일 열기 (비디오 파일 또는 웹캠 사용, 여기서는 웹캠 사용)
cap = cv2.VideoCapture(0)  # 웹캠을 사용하여 영상 캡처

while True:
    ret, frame = cap.read()  # 비디오 프레임 읽기
    if not ret:  # 프레임을 읽지 못했을 경우 루프 종료
        break

    frame = cv2.resize(frame, (1020, 600))  # 프레임 크기 조정

    # YOLOv8 추적 실행, 프레임 간 추적을 유지
    results = model.track(frame, persist=True)

    # 결과에서 박스가 있는지 확인
    if results[0].boxes is not None and results[0].boxes.id is not None:
        # 박스 정보 (x, y, w, h), 클래스 ID, 추적 ID, 신뢰도 추출
        boxes = results[0].boxes.xyxy.int().cpu().tolist()  # 바운딩 박스 좌표
        class_ids = results[0].boxes.cls.int().cpu().tolist()  # 클래스 ID
        track_ids = results[0].boxes.id.int().cpu().tolist()  # 추적 ID
        confidences = results[0].boxes.conf.cpu().tolist()  # 신뢰도 점수

        for box, class_id, track_id, conf in zip(boxes, class_ids, track_ids, confidences):
            c = names[class_id]  # 클래스 이름 가져오기
            x1, y1, x2, y2 = box  # 바운딩 박스 좌표 분리
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)  # 바운딩 박스 그리기
            cvzone.putTextRect(frame, f'{track_id}', (x1, y2), 1, 1)  # 추적 ID 텍스트 추가
            cvzone.putTextRect(frame, f'{c}', (x1, y1), 1, 1)  # 클래스 이름 텍스트 추가

    cv2.imshow("RGB", frame)  # 화면 표시
    
    # 프레임 업데이트 속도를 위해 waitKey를 1로 설정
    if cv2.waitKey(1) & 0xFF == ord("q"):  # 'q' 키 입력 시 종료
        break

# 비디오 캡처 객체 해제 및 디스플레이 창 닫기
cap.release()
cv2.destroyAllWindows()
