import cv2
from fireDetector import FireDetector


def main():
    detector = FireDetector()
    detector.initialize_camera()

    while True:
        ret, frame = detector.cap.read()
        if not ret:
            break
            
        processed_frame, fire_detected = detector.fireDetect(frame)
        
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
