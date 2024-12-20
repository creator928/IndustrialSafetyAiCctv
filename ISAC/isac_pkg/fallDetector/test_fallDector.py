import cv2
import time
from fallDetector import ISAC_FallDetector 

# 초기화
fall_detector = ISAC_FallDetector()  # ISAC_FallDect 클래스 인스턴스 생성

def main():
    # 웹캠 열기
    cap = cv2.VideoCapture(4)  # 0번 카메라를 엽니다. 다른 장치를 사용할 경우 번호를 변경하세요.

    if not cap.isOpened():
        print("웹캠을 열 수 없습니다.")
        return

    print("웹캠이 정상적으로 시작되었습니다. 'q'를 눌러 종료하세요.")
    
    # 프로그램 시작 시간 기록
    start_time = time.time()

    while True:
        ret, frame = cap.read()  # 웹캠에서 프레임 읽기
        if not ret:
            print("프레임을 읽을 수 없습니다. 프로그램을 종료합니다.")
            break

        # `cropped_img`를 기본값 `None`으로 초기화
        cropped_img = None
        work_info = {}  # work_info 기본값 초기화

        try:
            # fallDetect 메서드 호출하여 결과 처리
            detected_img, cropped_img, is_fall, work_info = fall_detector.fallDetect(frame)
        except Exception as e:
            print(f"오류 발생: {e}")
            detected_img = frame  # 오류 발생 시 원본 프레임을 출력
            work_info['error'] = str(e)  # 오류 정보를 work_info에 저장

        
        # 결과 화면 표시
        cv2.imshow("Fall Detection", detected_img)
        
        # 프로그램 시작 후 2초 이상 지난 경우에만 크롭 이미지 표시
        if time.time() - start_time > 2:
            if cropped_img is not None:
                cv2.imshow("Cropped Image", cropped_img)

        # 터미널에 work_info 출력
        if work_info is not None:
            print("Work Info:", work_info)
        

        # 'q'를 누르면 종료
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("프로그램을 종료합니다.")
            break

    # 자원 해제
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()