import cv2
from ISACgearDector import ISAC_GearDect  # Ensure `solo.py` is in the same directory or properly imported.

def main():
    # Initialize the ISAC_GearDect class
    helmet_detector = ISAC_GearDect()

    # Open the webcam
    cap = cv2.VideoCapture(0)  # Replace with the correct camera index if necessary.

    if not cap.isOpened():
        print("Unable to open the webcam.")
        return

    print("Webcam started. Press 'q' to quit.")

    while True:
        ret, frame = cap.read()  # Read a frame from the webcam
        if not ret:
            print("Unable to read a frame. Exiting.")
            break

        # Use the fallDetect method to process the frame
        processed_frame,helmet_results = helmet_detector.process(frame)

        # Display the processed frame
        cv2.imshow("Helmet Detection", processed_frame)
        print(helmet_results)

        # Exit the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Exiting.")
            break

    # Release resources
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

