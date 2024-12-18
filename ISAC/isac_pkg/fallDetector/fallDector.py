import cv2
from ultralytics import YOLO
import lap # track에 필요한 것
import time # 시간 측정

# region 글로벌 변수 선언
MODEL= YOLO("yolo11n.pt")  # YOLO11s 모델
fall_durations = {}
# endregion 글로벌 변수 끝


class ISAC_FallDetector():
    def __init__(self):
        pass

    def fallDetect(self, img):
        global MODEL
        global fall_durations
        cropped_bbxy = []
        cls_names = MODEL.names
        detected_img = img.copy()
        cropped_img = 0  # 기본값 0
        is_fall = [(0, False)]

        try:
            detected_result = MODEL.track(img, verbose=False, persist=True)
            if not detected_result or len(detected_result[0].boxes) == 0:
                return detected_img, cropped_img, is_fall

            for r in detected_result:
                box = r.boxes
                for b in box:
                    conf = float(b.conf[0].item() * 100)
                    if conf > 50:
                        try:
                            x1, y1, x2, y2 = b.xyxy[0].cpu().numpy()
                            cls_id = int(b.cls[0].item())
                            cls_name = cls_names[cls_id]
                            obj_id = int(b.id[0].item())  # 객체 ID 추출

                            # 넘어짐 처리 로직
                            if cls_name == "person":
                                person_h = y2 - y1
                                person_w = x2 - x1
                                person_thr = person_h - person_w
                                current_time = time.time()

                                if person_thr <= 0:
                                    if obj_id not in fall_durations:
                                        fall_durations[obj_id] = current_time
                                    fall_due = current_time - fall_durations[obj_id]

                                    if fall_due >= 5:
                                        color = (0, 0, 255)
                                        cropped_img = img[int(y1):int(y2), int(x1):int(x2)]
                                        is_fall = [(0, True)]
                                    elif fall_due >= 2:
                                        color = (0, 255, 255)
                                    else:
                                        color = (0, 255, 0)
                                else:
                                    if obj_id in fall_durations:
                                        del fall_durations[obj_id]
                                    color = (0, 255, 0)

                                cv2.rectangle(detected_img, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                                cv2.putText(detected_img, f"{cls_name} ({conf:.2f}%)",
                                            (int((x1 + x2) // 2 * 0.85), int(y1) - 10),
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
                        except Exception as e:
                            pass
        except Exception as e:
            pass

        return detected_img, cropped_img, is_fall #detected_img=원본 나머지는 = 0
