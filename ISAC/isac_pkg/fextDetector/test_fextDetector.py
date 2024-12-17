import os
import cv2
from fextDetector import ISAC_FextDetector  # ISAC_SafetyMonitor 클래스 임포트

# 클래스 초기화: 모델 경로는 fireDetector.py 내부에서 처리됨
safety_monitor = ISAC_FextDetector()

# 웹캠 초기화
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

print("Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Could not read frame.")
        break

    # 안전 상태 감지
    annotated_frame, emergency_status = safety_monitor.fextDetect(frame)

    # 상태 출력 (5초마다 상태가 출력됨)
    if emergency_status == 0:
        print("안전: 소화기와 사람이 모두 감지되었습니다.")
    elif emergency_status == 1:
        print("위험: 사람만 감지되었고 소화기가 없습니다.")
    elif emergency_status == 2:
        print("비정상 상태: 사람이 감지되지 않았습니다.")

    # 화면 표시
    cv2.imshow("Safety Monitor", annotated_frame)

    # 'q' 키로 종료
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 리소스 해제
cap.release()
cv2.destroyAllWindows()
