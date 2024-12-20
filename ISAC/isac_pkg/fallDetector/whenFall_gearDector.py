import cv2
import numpy as np
import pandas as pd
import os
from ultralytics import YOLO

class HelmetDetector():
    def __init__(self, model_path="best_helmet.pt", csv_filename="work_info.csv"):
        self.model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), model_path)
        self.model = YOLO(self.model_path)  # YOLO 모델 로드
        self.names = self.model.model.names  # 클래스 이름 로드
        self.csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), csv_filename)
        self.color_ranges = {
            "Blue": [(np.array([100, 150, 50]), np.array([140, 255, 255]))],
            "Green": [(np.array([40, 100, 50]), np.array([80, 255, 255]))],
            "Yellow": [(np.array([20, 100, 50]), np.array([40, 255, 255]))],
            "White": [(np.array([0, 0, 200]), np.array([180, 50, 255]))]        
        }
        self.rotation_angles = [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330]

    def load_worker_data(self):
        return pd.read_csv(self.csv_path)

    def rotate_image(self, image, angle):
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        return cv2.warpAffine(image, rotation_matrix, (w, h))

    def detect_highest_conf_helmet(self, image):
        highest_conf = 0
        best_crop = None
        results = self.model.predict(image, verbose=False)

        if results[0].boxes is not None:
            boxes = results[0].boxes.xyxy.int().cpu().tolist()
            class_ids = results[0].boxes.cls.int().cpu().tolist()
            confidences = results[0].boxes.conf.cpu().tolist()

            for box, class_id, conf in zip(boxes, class_ids, confidences):
                if self.names[class_id] == "Helmet" and conf > highest_conf:
                    x1, y1, x2, y2 = box
                    best_crop = image[y1:y2, x1:x2].copy()
                    highest_conf = conf

        return highest_conf, best_crop

    def segment_and_detect_colors(self, image, worker_data):
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        lower_white = self.color_ranges["White"][0][0]
        upper_white = self.color_ranges["White"][0][1]

        mask = cv2.inRange(hsv, lower_white, upper_white)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            largest_contour = max(contours, key=cv2.contourArea)

            segmented_image = np.zeros_like(image)
            cv2.drawContours(segmented_image, [largest_contour], -1, (255, 255, 255), thickness=cv2.FILLED)

            x, y, w, h = cv2.boundingRect(largest_contour)
            cropped_image = image[y:y+h, x:x+w]

            hsv_cropped = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2HSV)
            color_areas = {}

            for color_name, ranges in self.color_ranges.items():
                if color_name == "White":
                    continue
                mask = sum([cv2.inRange(hsv_cropped, lower, upper) for lower, upper in ranges])
                color_areas[color_name] = cv2.countNonZero(mask)

            most_dominant_color = max(color_areas, key=color_areas.get, default=None)
            if most_dominant_color:
                return most_dominant_color

        return None

    def process_image(self, image_path):
        frame = cv2.imread(image_path)
        if frame is None:
            print(f"Error: Could not read the image at {image_path}.")
            return {}

        worker_data = self.load_worker_data()

        best_helmet_conf, best_helmet_image = 0, None

        for angle in self.rotation_angles:
            rotated_frame = self.rotate_image(frame, angle)
            conf, crop = self.detect_highest_conf_helmet(rotated_frame)
            if conf > best_helmet_conf:
                best_helmet_conf, best_helmet_image = conf, crop

        if best_helmet_image is not None:
            most_dominant_color = self.segment_and_detect_colors(best_helmet_image, worker_data)

            if most_dominant_color:
                matching_workers = worker_data[worker_data['Helmet_Color'] == most_dominant_color]
                return matching_workers.to_dict(orient="records")

        return {"error": "No Helmet detected."}