import os
import cv2
from ultralytics import YOLO
import lap  # track에 필요한 것
import time  # 시간 측정
from whenFall_gearDector import HelmetDetector

helmet_detector = HelmetDetector()

# region 글로벌 변수 선언
model_dir = base_dir = os.path.join(os.path.dirname(__file__), "fallDetector")
model_file = "yolo11s.pt"  # 모델 파일 이름
model_path = os.path.join(model_dir, model_file)  # 전체 경로 동적으로 생성

# YOLO 모델 초기화
MODEL = YOLO(model_path)  # 동적으로 생성된 경로로 모델 로드
fall_durations = {}  # {obj_id: (start_time, is_fall_notified)}

class ISAC_FallDetector():
    def __init__(self):
        pass

    def fallDetect(self, img):
        """
        넘어짐 감지 메서드
        """
        global MODEL
        global fall_durations

        cropped_bbxy = []
        cls_names = MODEL.names
        detected_img = img.copy()
        work_info = None
        cropped_img = None
        is_fall = [(0, False)]

        try:
            detected_result = MODEL.track(img, verbose=False, persist=True)

            if not detected_result or len(detected_result[0].boxes) == 0:
                return detected_img, cropped_img, is_fall, work_info

            for r in detected_result:
                box = r.boxes
                for b in box:
                    conf = float(b.conf[0].item() * 100)

                    if conf > 50:
                        try:
                            x1, y1, x2, y2 = b.xyxy[0].cpu().numpy()
                            cls_id = int(b.cls[0].item())
                            cls_name = cls_names[cls_id]
                            obj_id = int(b.id[0].item())
                            

                            if cls_name == "person":
                                person_h = y2 - y1
                                person_w = x2 - x1
                                person_thr = person_h - person_w
                                current_time = time.time()

                                if person_thr <= 0:
                                    try:
                                        if obj_id not in fall_durations:
                                            fall_durations[obj_id] = (current_time, False)

                                        fall_start_time, notified = fall_durations[obj_id]
                                        fall_due = current_time - fall_start_time

                                        if fall_due >= 5:
                                            color = (0, 0, 255)
                                            cropped_img = img[int(y1):int(y2), int(x1):int(x2)]
                                            try:
                                                if not notified:
                                                    is_fall = [(0, True)]
                                                    fall_durations[obj_id] = (fall_start_time, True)

                                                    # 바운딩 박스 확장
                                                    # y축으로만 확장
                                                    margin = 200  # y축 확장 마진
                                                    h, w = img.shape[:2]  # 이미지 크기 (높이, 너비)

                                                    # y좌표 확장
                                                    y1_expanded = max(0, int(y1) - margin)  # y1을 위로 확장
                                                    y2_expanded = min(h, int(y2) + margin)  # y2를 아래로 확장
 
                                                    # x좌표는 그대로 유지
                                                    x1_expanded = max(0, int(x1) - margin)  # x1을 왼쪽으로 확장
                                                    x2_expanded = min(w, int(x2) + margin)  # x2를 오른쪽으로 확장

                                                    # 확장된 바운딩 박스 적용
                                                    cropped_img_expand = img[y1_expanded:y2_expanded, x1_expanded:x2_expanded]

                                                    # 로컬에 저장
                                                    cropped_img_expand = img[y1_expanded:y2_expanded, x1_expanded:x2_expanded]
                                                    base_dir = os.path.join(os.path.dirname(__file__), "fallDetector")
                                                    os.makedirs(base_dir, exist_ok=True)
                                                    save_path = f"cropped_person.jpg"
                                                    cv2.imwrite(save_path, cropped_img_expand)
                                                    work_info = helmet_detector.process_image(save_path)
                                            except Exception as e:
                                                pass

                                        elif fall_due >= 2:
                                            color = (0, 255, 255)
                                            cropped_img = img[int(y1):int(y2), int(x1):int(x2)]
                                        else:
                                            color = (0, 255, 0)
                                    except Exception as e:
                                        pass
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

        return detected_img, cropped_img, is_fall, work_info