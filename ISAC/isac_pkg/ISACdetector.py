import cv2
from ultralytics import YOLO
import lap # track에 필요한 것
import time # 시간 측정

# region 글로벌 변수 선언
MODEL= YOLO("yolo11s.pt")  # YOLO11n 모델
# endregion 글로벌 변수 끝

class ISAC():
    def __init__(self):
        pass

    def detectAll(self, image):
        """
        이미지를 받아 탐지한 이미지를 반환하는 메서드
        Args:
            image : VideoCapture로부터 read 한 이미지
        Returns:
            detected_image : YOLO로부터 디텍팅 한 결과 이미지
        """
        global MODEL
        detected_result = MODEL(image, verbose=False) # 모델 YOLO 기반 디텍팅 결과 저장
        detected_image = detected_result[0].plot()  # 결과를 시각화하여 프레임에 그리기
        return detected_image
    
    def detectFilter(self, image, filter):
        """
        이미지와 필터링 리스트를 받아 특정 객체만 탐지한 이미지를 반환하는 메서드
        필터링 리스트 예시 : filter = ["person", "bottle", "cell phone"]
        Args:
            image : VideoCapture로부터 read 한 이미지
            filter : YOLO에서 분류한 classification 명칭
        Returns:
            detected_image : YOLO로부터 디텍팅 한 결과 이미지
        """
        global MODEL
        cls_names = MODEL.names # YOLO에서 구분 가능한 클래시피케이션 리스트 호출
        detected_result = MODEL(image, verbose=False) # 모델 YOLO 기반 디텍팅 결과 저장
        detected_image = image.copy() # 결과 이미지 저장용 사본
        for result in detected_result:
            boxes = result.boxes # 박스 정보 저장
            for box in boxes:
                conf = box.conf[0] * 100 # 해당 객체의 신뢰도 (백분률 전환)
                if conf > 50: # 신뢰도가 50이상일 때
                    x1, y1, x2, y2 = box.xyxy[0]  # bounding box 시작xy, 끝xy 좌표
                    cls_id = int(box.cls[0]) # 클래스 인덱스(YOLO 클래시피케이션 id)
                    cls_name = cls_names[cls_id] # 클래스 id에 따른 name 가져옴
                    if cls_name in filter: # 만약 필터링 리스트에 cls 네임이 있다면
                        detct_info = f"{cls_name} ({conf:.2f}%)"
                        if cls_name == "person":
                            cv2.rectangle(detected_image, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                            cv2.putText(detected_image, detct_info, (int((x1+x2)//2*0.85), int(y1)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 10)
                            cv2.putText(detected_image, detct_info, (int((x1+x2)//2*0.85), int(y1)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
                        elif cls_name == "":
                            # 필터에 사용한 것중 필요한 것들을 elif로 추가
                            pass
                        else:
                            cv2.rectangle(detected_image, (int(x1), int(y1)), (int(x2), int(y2)), (255, 50, 50), 2)
                            cv2.putText(detected_image, detct_info, (int((x1+x2)//2*0.85), int(y1)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 10)
                            cv2.putText(detected_image, detct_info, (int((x1+x2)//2*0.85), int(y1)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        return detected_image
