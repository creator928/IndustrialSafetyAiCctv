from KBG_PE import ISAC_PoseEstimator
import cv2


# ISAC 클래스 초기화
pose_estimator = ISAC_PoseEstimator(model_path="yolo11s-pose.pt")

# 웹캠 초기화
cap = cv2.VideoCapture(0)  # 0번 카메라 사용

if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

print("Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Could not read frame.")
        break

    # 도움 요청 여부 및 객체 ID 감지
    help_sign_data = pose_estimator.helpDetect(frame)

    # 결과 출력
    for person_id, help_sign in help_sign_data:
        print(f"Person {person_id}: HELP_SIGN = {help_sign}")

    # 결과 프레임 표시
    cv2.imshow("Webcam - Pose Detection", frame)

    # 'q' 키를 누르면 종료
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 자원 해제
cap.release()
cv2.destroyAllWindows()
