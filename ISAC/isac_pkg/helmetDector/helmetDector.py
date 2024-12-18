import tkinter as tk
import cv2
import numpy as np
import pandas as pd
import os
from ultralytics import YOLO



class ISAC_DectHelmet():
    def __init__(self, modelPath="best_helmet.pt", csvFilename="work_info.csv"):
        """
        RotatePP 클래스 초기화
        :param modelPath: YOLO 모델 경로
        :param csvFilename: 작업자 정보 CSV 파일 이름
        """
        self.model = YOLO(modelPath)  # YOLO 모델 로드
        self.names = self.model.model.names  # YOLO 클래스 이름 로드
        self.csvPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), csvFilename)
        self.colorRanges = {
            "Red": [(np.array([0, 100, 50]), np.array([10, 255, 255])),
                    (np.array([170, 100, 50]), np.array([180, 255, 255]))],
            "Blue": [(np.array([100, 150, 50]), np.array([140, 255, 255]))],
            "Green": [(np.array([40, 100, 50]), np.array([80, 255, 255]))],
            "Yellow": [(np.array([20, 100, 50]), np.array([40, 255, 255]))],
            "Black": [(np.array([0, 0, 0]), np.array([180, 255, 50]))],
            "White": [(np.array([0, 0, 200]), np.array([180, 50, 255]))]
        }
        self.rotationAngles = [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330]

    def loadWorkerData(self):
        """CSV 파일에서 작업자 데이터 로드"""
        return pd.read_csv(self.csvPath)

    def rotateImage(self, image, angle):
        """이미지를 특정 각도로 회전"""
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        rotationMatrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        return cv2.warpAffine(image, rotationMatrix, (w, h))

    def detectHighestConfHelmet(self, image):
        """최고 컨피던스를 가진 헬멧 탐지"""
        highestConf = 0
        bestCrop = None
        results = self.model.predict(image, verbose=False)

        if results[0].boxes is not None:
            boxes = results[0].boxes.xyxy.int().cpu().tolist()
            classIds = results[0].boxes.cls.int().cpu().tolist()
            confidences = results[0].boxes.conf.cpu().tolist()

            for box, classId, conf in zip(boxes, classIds, confidences):
                if self.names[classId] == "Helmet" and conf > highestConf:
                    x1, y1, x2, y2 = box
                    bestCrop = image[y1:y2, x1:x2].copy()
                    highestConf = conf

        return highestConf, bestCrop

    def combineLargestWhiteBoxes(self, image):
        """가장 큰 두 개의 흰색 바운딩 박스를 결합"""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.colorRanges["White"][0][0], self.colorRanges["White"][0][1])
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        largestBoxes = sorted([cv2.boundingRect(cnt) for cnt in contours if cv2.contourArea(cnt) > 500],
                               key=lambda b: b[2] * b[3], reverse=True)[:2]

        if len(largestBoxes) == 2:
            x1, y1, w1, h1 = largestBoxes[0]
            x2, y2, w2, h2 = largestBoxes[1]
            xMin, yMin = min(x1, x2), min(y1, y2)
            xMax, yMax = max(x1 + w1, x2 + w2), max(y1 + h1, y2 + h2)

            combinedBox = image[yMin:yMax, xMin:xMax].copy()
            return combinedBox
        return None

    def detectLargestColorExcludingWhite(self, image):
        """흰색 제외 가장 큰 색상 탐지"""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        largestArea, largestBox, largestColor = 0, None, None

        for colorName, ranges in self.colorRanges.items():
            if colorName == "White":
                continue
            mask = sum([cv2.inRange(hsv, lower, upper) for lower, upper in ranges])
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area > largestArea:
                    largestArea, largestBox, largestColor = area, cv2.boundingRect(cnt), colorName

        return largestColor

    def processFrame(self, frame):
        """프레임을 처리하고 작업자 정보를 반환"""
        workersDf = self.loadWorkerData()

        bestHelmetConf, bestHelmetImage = 0, None
        for angle in self.rotationAngles:
            rotatedFrame = self.rotateImage(frame, angle)
            conf, crop = self.detectHighestConfHelmet(rotatedFrame)
            if conf > bestHelmetConf:
                bestHelmetConf, bestHelmetImage = conf, crop

        if bestHelmetImage is not None:
            combinedBox = self.combineLargestWhiteBoxes(bestHelmetImage)
            if combinedBox is not None:
                detectedColor = self.detectLargestColorExcludingWhite(combinedBox)
                if detectedColor:
                    matchingWorkers = workersDf[workersDf['Helmet_Color'] == detectedColor]
                    return matchingWorkers.to_dict(orient="records")
        return []
