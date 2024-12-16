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
        global fall_durations  # 넘어짐 시간 저장용 딕셔너리
        cropped_bbxy = []  # [x1, y1, x2, y2]를 리스트로 저장
        cls_names = MODEL.names  # YOLO에서 구분 가능한 클래시피케이션 리스트 호출
        detected_result = MODEL.track(img, verbose=False, persist=True)  # persist 옵션을 통해 추적
        detected_img = img.copy()  # 결과 이미지 저장용 img 복제
        cropped_img = None  # 초기값

        for r in detected_result:
            box = r.boxes
            for b in box:
                conf = float(b.conf[0].item() * 100)  # 신뢰도를 float로 변환
                if conf > 50:  # 신뢰도가 50 이상일 때
                    # 좌표를 numpy 배열로 변환
                    x1, y1, x2, y2 = b.xyxy[0].cpu().numpy()
                    cls_id = int(b.cls[0].item())  # 클래스 ID 추출
                    cls_name = cls_names[cls_id]  # 클래스 이름 호출
                    obj_id = int(b.id[0].item())  # 객체 ID 추출
                    detct_info = f"{cls_name} ({conf:.2f}%)"  # 출력 정보

                    if cls_name == "person":  # 넘어짐 대상 person
                        person_h = y2 - y1  # 높이
                        person_w = x2 - x1  # 너비
                        person_thr = person_h - person_w  # 높이 - 너비 스레스홀드
                        current_time = time.time()  # 현재 시간 호출

                        if person_thr <= 0:  # 스레스홀드가 음수일 경우
                            if obj_id not in fall_durations:  # 글로벌 변수 딕셔너리에 id가 없을 경우
                                fall_durations[obj_id] = current_time  # 현재 시간을 id에 맞춰 저장
                            fall_due = current_time - fall_durations[obj_id]

                            if fall_due >= 5:
                                color = (0, 0, 255)
                                cropped_img = img[int(y1):int(y2), int(x1):int(x2)]  # 5초 이상 넘어짐
                            elif fall_due >= 2:
                                color = (0, 255, 255)
                                cropped_img = None
                            else:
                                color = (0, 255, 0)
                                cropped_img = None
                        else:
                            if obj_id in fall_durations:
                                del fall_durations[obj_id]
                            color = (0, 255, 0)
                            cropped_img = None

                        cv2.rectangle(detected_img, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                        cv2.putText(detected_img, detct_info, (int((x1 + x2) // 2 * 0.85), int(y1) - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 10)
                        cv2.putText(detected_img, detct_info, (int((x1 + x2) // 2 * 0.85), int(y1) - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
                    else:
                        # cv2.rectangle(detected_img, (int(x1), int(y1)), (int(x2), int(y2)), (255, 50, 50), 2)
                        # cv2.putText(detected_img, detct_info, (int((x1 + x2) // 2 * 0.85), int(y1) - 10),
                        #             cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 10)
                        # cv2.putText(detected_img, detct_info, (int((x1 + x2) // 2 * 0.85), int(y1) - 10),
                        #             cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
                        cropped_img = None
                        pass

        return detected_img, cropped_img


   
