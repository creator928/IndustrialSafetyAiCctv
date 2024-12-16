import cv2
import numpy as np
from ultralytics import YOLO
import cvzone
import time

# YOLOv8 모델 로드
model = YOLO("yolo11s.pt")
names = model.model.names

# 비디오 파일 열기 (비디오 파일 또는 웹캠 사용, 여기서는 웹캠 사용)
cap = cv2.VideoCapture(0)

# VideoWriter를 위한 코덱 정의 및 프레임 속도 조정
# fourcc = cv2.VideoWriter_fourcc(*'mp4')
# input_frame_rate = 30  
# output_frame_rate = input_frame_rate // 3  # 프레임 스킵을 위한 조정 (30 / 3 = 10 FPS)
# out = cv2.VideoWriter('output_fall_detection.mp4', fourcc, output_frame_rate, (1020, 600))

# 추락 감지를 위한 변수 초기화
fall_durations = {}  # 트랙 ID별로 추락 시작 시간을 저장하는 사전
count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    count += 1
    if count % 3 != 0:  # 매 세 번째 프레임만 처리
        continue

    frame = cv2.resize(frame, (1020, 600))

    # 프레임에서 YOLOv8 추적 실행, 프레임 간 트랙 유지
    results = model.track(frame, persist=True, classes=0)

    # 결과에 박스가 있는지 확인
    if results[0].boxes is not None and results[0].boxes.id is not None:
        # 박스 (x, y, w, h), 클래스 ID, 트랙 ID, 신뢰도를 가져옴
        boxes = results[0].boxes.xyxy.int().cpu().tolist()  # 바운딩
        class_ids = results[0].boxes.cls.int().cpu().tolist()  # 클래스 ID
        track_ids = results[0].boxes.id.int().cpu().tolist()  # 트랙 ID
        confidences = results[0].boxes.conf.cpu().tolist()  # 신뢰도
        
        for box, class_id, track_id, conf in zip(boxes, class_ids, track_ids, confidences):
            c = names[class_id]
            x1, y1, x2, y2 = box
            h = y2 - y1
            w = x2 - x1
            thresh = h - w
            current_time = time.time()

            # 룰베이스 기반으로 추락 여부 결정
            if thresh <= 0:
                if track_id not in fall_durations:
                    fall_durations[track_id] = current_time  # 추락 지속 시간 측정 시작
                fall_duration = current_time - fall_durations[track_id]

                # 추락 지속 시간에 따라 박스 색상 설정
                if fall_duration >= 5:
                    color = (0, 0, 255)  # 추락 지속 시간이 5초 이상이면 빨간색
                elif fall_duration >= 2:
                    color = (0, 255, 255)  # 추락 지속 시간이 2초 이상이면 노란색
                else:
                    color = (0, 255, 0)  # 추락 지속 시간이 2초 미만이면 초록색

                # 적절한 색상으로 사각형을 그림
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                # 트랙 ID 및 추락 상태 표시
                cvzone.putTextRect(frame, f'{track_id}', (x1, y2), 1, 1)
                cvzone.putTextRect(frame, f"{'Fall'}", (x1, y1), 1, 1)

            else:
                # 추락이 감지되지 않으면 추락 지속 시간 초기화
                if track_id in fall_durations:
                    del fall_durations[track_id]
                # 정상 상태 - 초록색 경계 상자와 "Normal" 텍스트 표시
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cvzone.putTextRect(frame, f'{track_id}', (x1, y2), 1, 1)
                cvzone.putTextRect(frame, f"{'Normal'}", (x1, y1), 1, 1)

    # 윈도우에 프레임 표시
    cv2.imshow("RGB", frame)

    # 비디오 파일에 프레임 기록 (주석 처리됨)
    # out.write(frame)

    # 'q' 키가 눌리면 루프 종료
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# 비디오 캡처 및 비디오 쓰기 객체 해제
cap.release()
# out.release()  # 비디오 쓰기 해제 주석 처리
cv2.destroyAllWindows()  
