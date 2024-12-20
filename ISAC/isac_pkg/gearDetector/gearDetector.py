import cv2
from ultralytics import YOLO
import lap  # track에 필요한 것
import os

# region 글로벌 변수 선언
current_dir = os.path.dirname(os.path.abspath(__file__))
MODEL = YOLO(os.path.join(current_dir, "best_gear.pt"))  # YOLO11s 모델
MODEL2 = YOLO(os.path.join(current_dir, "yolo11n.pt"))  # YOLO11s 모델

class ISAC_GearDect():
    def __init__(self):
        pass

    def fallDetect(self, cropped_img):
        global MODEL

        # YOLO 모델 실행
        results = MODEL(cropped_img, verbose=False)
        gear_detected = False

        for result in results:
            if result.boxes is not None:  # boxes가 None이 아닌지 확인
                for box in result.boxes:  # 모든 box 순회
                    class_id = int(box.cls.cpu().numpy())  # 클래스 ID 가져오기
                    if class_id == 0:  # Gear
                        gear_detected = True
                    elif class_id == 1:  # No_Gear
                        gear_detected = False
                        break  # No_Gear 발견 시 바로 종료

        return gear_detected


    # 02. YOLO person 디텍션 & 크롭(이미지, 필터링 문자열 리스트)
    def yoloPersonDetect(self, img):
        global MODEL2
        cropped_bbxy = [] # [x1, y1, x2, y2]를 리스트로 저장
        cropped_img = [] # [x1, y1, x2, y2]로 자른 이미지들 저장
        cls_names = MODEL2.names # YOLO에서 구분 가능한 클래시피케이션 리스트 호출
        detected_result = MODEL2(img, verbose=False) # 모델 YOLO 기반 디텍팅 결과 저장
        detected_img = img.copy() # 결과 이미지 저장용 img 복제

        for r in detected_result:
            box = r.boxes # 박스 정보 저장
            for b in box:
                conf = b.conf[0] * 100 # 해당 객체의 신뢰도 (백분률 전환)
                cls_id = int(b.cls[0]) # 클래스 인덱스(YOLO 클래시피케이션 id)
                cls_name = cls_names[cls_id] # 클래스 id에 따른 name 가져옴

                if cls_name == "person":
                    if conf > 50: # 신뢰도가 50이상일 때
                        x1, y1, x2, y2 = b.xyxy[0]  # bounding box 시작xy, 끝xy
                        # 바운딩 박스 좌표 저장 xyxy
                        cropped_bbxy.append([int(x1), int(y1), int(x2), int(y2)])
                        # 바운딩 박스 영역으로 이미지를 크롭
                        cropped_img.append(img[int(y1):int(y2), int(x1):int(x2)])

        return detected_img, cropped_img, cropped_bbxy

    def process(self, img):
        detected_img, cropped_imgs, cropped_bbxy = self.yoloPersonDetect(img)

        gear_results = []
        if cropped_imgs:  # 사람이 감지된 경우에만 처리
            for (cropped, bbxy) in zip(cropped_imgs, cropped_bbxy):
                gear_detected = self.fallDetect(cropped)
                x1, y1, x2, y2 = bbxy
                if gear_detected:
                    color = (0, 255, 0)  # Green for gear
                else:
                    color = (0, 0, 255)  # Red for no gear
                cv2.rectangle(detected_img, (x1, y1), (x2, y2), color, 2)
                gear_results.append(gear_detected)

        # 튜플 형식으로 각 결과를 변환
        formatted_results = tuple(f'[{res}]' for res in gear_results)

        return detected_img, formatted_results
