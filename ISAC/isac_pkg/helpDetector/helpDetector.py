import cv2
from ultralytics import YOLO
import time

# YOLO 모델 초기화
MODEL = YOLO("yolo11s-pose.pt")  # 사용할 YOLOv8 모델 경로 지정


class ISAC_PoseEstimator:
    def __init__(self, model_path="yolo11s-pose.pt"):
        """
        클래스 초기화
        Args:
            model_path: YOLO 모델 파일 경로
        """
        self.model = YOLO(model_path)  # YOLO 모델 로드
        self.count_dict = {}  # 각 사람의 행동 카운트를 저장할 딕셔너리
        self.maintime_dict = {}  # 각 사람의 행동 시작 시간을 저장할 딕셔너리

    def findKeypoint(self, results):
        """
        YOLO 추론 결과로부터 각 관절 좌표를 추출
        Args:
            results: YOLO 모델의 추론 결과
        Returns:
            keypoints_data: 관절 좌표 리스트, 사람별로 구분된 데이터
        """
        # 관절 이름과 YOLO 인덱스를 매핑하는 딕셔너리
        body_parts = {
            0: "코 (Nose)",
            1: "왼쪽 눈 (Left Eye)",
            2: "오른쪽 눈 (Right Eye)",
            3: "왼쪽 귀 (Left Ear)",
            4: "오른쪽 귀 (Right Ear)",
            5: "왼쪽 어깨 (Left Shoulder)",
            6: "오른쪽 어깨 (Right Shoulder)",
            7: "왼쪽 팔꿈치 (Left Elbow)",
            8: "오른쪽 팔꿈치 (Right Elbow)",
            9: "왼쪽 손목 (Left Wrist)",
            10: "오른쪽 손목 (Right Wrist)",
            11: "왼쪽 엉덩이 (Left Hip)",
            12: "오른쪽 엉덩이 (Right Hip)",
            13: "왼쪽 무릎 (Left Knee)",
            14: "오른쪽 무릎 (Right Knee)",
            15: "왼쪽 발목 (Left Ankle)",
            16: "오른쪽 발목 (Right Ankle)"
        }

        # 추출된 관절 데이터를 저장할 리스트
        keypoints_data = []
        for person_idx, keypoints in enumerate(results[0].keypoints):
            # 키포인트 좌표 가져오기 (YOLO에서 추출된 각 관절의 x, y 좌표)
            kxy = keypoints.xy[0]
            # 좌표 데이터를 리스트로 변환 (각 관절의 (x, y) 튜플)
            kxy_list = [(row[0].item(), row[1].item()) for row in kxy]
            # 관절 이름과 좌표를 딕셔너리로 매핑
            kepoint_dict = {i: {"body_part": body_parts[i], "x,y": kxy_list[i]} for i in range(len(kxy_list))}
            # 사람 인덱스와 키포인트 딕셔너리를 리스트에 추가
            keypoints_data.append((person_idx, kepoint_dict))
        return keypoints_data

    def helpDetect(self, frame):
        """
        인체 관절 좌표를 분석하여 도움 요청 여부와 객체 ID를 반환
        Args:
            frame: 입력 이미지 프레임
        Returns:
            help_sign_data: 도움 요청 여부 및 객체 ID 리스트 ([(id, HELP_SIGN), ...])
        """
        help_sign_data = []  # 반환할 데이터 리스트

        # YOLO 모델을 사용하여 입력 프레임 추론
        results = self.model(frame, verbose=False)

        # 추론 결과로부터 관절 좌표 추출
        keypoints_data = self.findKeypoint(results)

        # 현재 시간
        now_time = time.time()

        # 추출된 각 사람의 관절 데이터를 순회하며 분석
        for person_idx, kepoint_dict in keypoints_data:
            HELP_SIGN = False  # 개별 객체의 도움 요청 여부 초기화

            # 필요한 좌표 추출
            nose_coordinates = kepoint_dict.get(0, {}).get("x,y")  # 코
            lw_coordinates = kepoint_dict.get(9, {}).get("x,y")  # 왼쪽 손목
            rw_coordinates = kepoint_dict.get(10, {}).get("x,y")  # 오른쪽 손목
            ls_coordinates = kepoint_dict.get(5, {}).get("x,y")  # 왼쪽 어깨
            rs_coordinates = kepoint_dict.get(6, {}).get("x,y")  # 오른쪽 어깨

            # 모든 관절 좌표가 유효한 경우에만 처리
            if all([nose_coordinates, lw_coordinates, rw_coordinates, ls_coordinates, rs_coordinates]):
                # 손목의 y 좌표가 코의 y 좌표보다 높고, 손목의 x 좌표가 어깨보다 멀 경우
                if (
                    lw_coordinates[1] < nose_coordinates[1] and
                    rw_coordinates[1] < nose_coordinates[1] and
                    lw_coordinates[0] > ls_coordinates[0] and
                    rw_coordinates[0] < rs_coordinates[0]
                ):
                    # 새로운 사람의 행동 시작
                    if person_idx not in self.maintime_dict:
                        self.maintime_dict[person_idx] = now_time
                        self.count_dict[person_idx] = 1
                    else:
                        # 기존 사람의 행동 유지
                        self.count_dict[person_idx] += 1
                        # 손을 들고 있는 시간이 3초 이상이면 HELP_SIGN을 True로 유지
                        if now_time - self.maintime_dict[person_idx] >= 3:
                            HELP_SIGN = True

                else:
                    # 손을 내렸을 경우 시간 초기화
                    self.maintime_dict[person_idx] = now_time
                    self.count_dict[person_idx] = 0

            # HELP_SIGN 데이터에 (ID, 상태) 추가
            help_sign_data.append((person_idx, HELP_SIGN))

        return help_sign_data  # 도움 요청 여부 및 객체 ID 리스트 반환




"""
from isac_pose_estimator import ISAC_PoseEstimator

# ISAC 클래스 초기화
pose_estimator = ISAC_PoseEstimator(model_path="yolo11s-pose.pt")

# 테스트 이미지 로드
test_frame = cv2.imread("test_image.jpg")

# 도움 요청 여부 감지
help_sign = pose_estimator.helpDetect(test_frame)

# 결과 출력
print(f"HELP_SIGN Detected: {help_sign}")

"""