import cv2
import numpy as np
import pandas as pd
import os
from ultralytics import YOLO

class ISAC_DectHelmet:
    def __init__(self, model_path="best.pt", csv_filename="work_info.csv"):
        self.model = YOLO(os.path.join(os.path.dirname(os.path.abspath(__file__)), model_path))  # YOLO 모델 로드
        self.names = self.model.model.names  # 클래스 이름 로드
        self.csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), csv_filename)  # CSV 파일 경로 설정
        self.colorRanges = {
            "Blue": [(np.array([100, 150, 50]), np.array([140, 255, 255]))],  # 파란색 HSV 범위
            "Green": [(np.array([40, 100, 50]), np.array([80, 255, 255]))],  # 초록색 HSV 범위
            "Yellow": [(np.array([20, 100, 50]), np.array([40, 255, 255]))],  # 노란색 HSV 범위
            "White": [(np.array([0, 0, 200]), np.array([180, 50, 255]))],  # 흰색 HSV 범위
            "Orange": [(np.array([10, 100, 50]), np.array([20, 255, 255]))],  # 주황색 HSV 범위
            "Pink": [(np.array([160, 100, 50]), np.array([170, 255, 255]))],  # 분홍색 HSV 범위
            "Gray": [(np.array([0, 0, 50]), np.array([180, 50, 200]))],  # 회색 HSV 범위
        }
        self.rotationAngles = [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330]  # 회전 각도 설정

    def loadWorkerData(self):
        return pd.read_csv(self.csv_path)  # 작업자 데이터 로드

    def rotateImage(self, image, angle):
        (h, w) = image.shape[:2]  # 이미지 높이와 너비 가져오기
        center = (w // 2, h // 2)  # 이미지 중심 계산
        rotationMatrix = cv2.getRotationMatrix2D(center, angle, 1.0)  # 회전 행렬 생성
        return cv2.warpAffine(image, rotationMatrix, (w, h))  # 회전 적용

    def detectHighestConfHelmet(self, image):
        highestConf = 0  # 최고 신뢰도 초기화
        bestCrop = None  # 최고 신뢰도를 가진 이미지 초기화
        results = self.model.predict(image, verbose=False)  # YOLO 모델 예측

        if results[0].boxes is not None:  # 감지된 객체가 있을 경우
            boxes = results[0].boxes.xyxy.int().cpu().tolist()  # 객체의 바운딩 박스 좌표
            classIds = results[0].boxes.cls.int().cpu().tolist()  # 객체 클래스 ID
            confidences = results[0].boxes.conf.cpu().tolist()  # 객체 신뢰도

            for box, classId, conf in zip(boxes, classIds, confidences):
                if self.names[classId] == "Helmet" and conf > highestConf:  # 헬멧 클래스 확인 및 신뢰도 비교
                    x1, y1, x2, y2 = box
                    bestCrop = image[y1:y2, x1:x2].copy()  # 최고 신뢰도를 가진 영역 크롭
                    highestConf = conf

        return highestConf, bestCrop  # 최고 신뢰도와 크롭된 이미지 반환

    def segmentAndDetectColors(self, image, workerData):
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)  # 이미지를 HSV로 변환
        lowerWhite = self.colorRanges["White"][0][0]  # 흰색 범위 하한값
        upperWhite = self.colorRanges["White"][0][1]  # 흰색 범위 상한값

        mask = cv2.inRange(hsv, lowerWhite, upperWhite)  # 흰색 마스크 생성
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)  # 외곽선 감지

        if contours:
            largestContour = max(contours, key=cv2.contourArea)  # 가장 큰 외곽선 선택

            segmentedImage = np.zeros_like(image)  # 분리된 이미지 초기화
            cv2.drawContours(segmentedImage, [largestContour], -1, (255, 255, 255), thickness=cv2.FILLED)  # 외곽선 채우기

            x, y, w, h = cv2.boundingRect(largestContour)  # 바운딩 박스 계산
            croppedImage = image[y:y+h, x:x+w]  # 바운딩 박스 크롭

            hsvCropped = cv2.cvtColor(croppedImage, cv2.COLOR_BGR2HSV)  # 크롭된 이미지 HSV 변환
            colorAreas = {}

            for colorName, ranges in self.colorRanges.items():
                if colorName == "White":
                    continue  # 흰색 제외
                mask = sum([cv2.inRange(hsvCropped, lower, upper) for lower, upper in ranges])  # 색상 범위 마스크 생성
                colorAreas[colorName] = cv2.countNonZero(mask)  # 색상 영역 픽셀 개수 계산

            mostDominantColor = max(colorAreas, key=colorAreas.get, default=None)  # 가장 많은 픽셀을 가진 색상 선택
            if mostDominantColor:
                return mostDominantColor  # 지배적인 색상 반환

        return None  # 색상 감지 실패 시 None 반환

    def processImage(self, imagePath):
        frame = cv2.imread(imagePath)  # 이미지 파일 읽기
        if frame is None:
            return {}

        workerData = self.loadWorkerData()  # 작업자 데이터 로드

        bestHelmetConf, bestHelmetImage = 0, None

        for angle in self.rotationAngles:  # 각도별로 이미지 회전
            rotatedFrame = self.rotateImage(frame, angle)
            conf, crop = self.detectHighestConfHelmet(rotatedFrame)  # 회전된 이미지에서 헬멧 감지
            if conf > bestHelmetConf:
                bestHelmetConf, bestHelmetImage = conf, crop  # 최고 신뢰도 업데이트

        if bestHelmetImage is not None:
            mostDominantColor = self.segmentAndDetectColors(bestHelmetImage, workerData)  # 색상 분석

            if mostDominantColor:
                matchingWorkers = workerData[workerData['Helmet_Color'] == mostDominantColor]  # 작업자 정보 매칭
                return matchingWorkers.to_dict(orient="records")  # 작업자 정보 반환

        return {"error": "No Helmet detected."}  # 헬멧 감지 실패 시 에러 메시지 반환
