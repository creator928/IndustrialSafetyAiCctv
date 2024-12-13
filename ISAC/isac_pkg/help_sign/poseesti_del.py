import cv2
from ultralytics import YOLO
import time


first_time = time.time()
count = 0
maintime = None

model = YOLO('yolo11s-pose.pt') 

cap = cv2.VideoCapture(0) 

if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Could not read frame.")
        break

    results = model.track(frame, verbose=False, persist=True)

    annotated_frame = results[0].plot()  

    keypoints = results[0].keypoints[0]  
    
    kxy = keypoints.xy[0] 

    kxy_list = [(row[0].item(), row[1].item()) for row in kxy]  

    #print(kxy_list)  # 리스트 테스트 출력

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

    if results is not None:
        if kxy_list is not None:
            # ----- 키 포인트 리스트와 바디 파츠 리스트를 하나의 딕셔너리로 합성 ------
            kepoint_dict = {i: {"body_part": body_parts[i], "x,y": kxy_list[i]} for i in range(len(kxy_list))}

            if 0 in kepoint_dict and kepoint_dict[0]["x,y"] != (0, 0):
                nose_coordinates = kepoint_dict[0]["x,y"]
            else:
                pass

            # 왼쪽 손목 좌표 검증 및 출력
            if 9 in kepoint_dict and kepoint_dict[9]["x,y"] != (0, 0):
                lw_coordinates = kepoint_dict[9]["x,y"]
            else:
                pass

            # 오른쪽 손목 좌표 검증 및 출력
            if 10 in kepoint_dict and kepoint_dict[10]["x,y"] != (0, 0):
                rw_coordinates = kepoint_dict[10]["x,y"]
            else:
                pass

            # 왼쪽 어깨 좌표 검증 및 출력
            if 5 in kepoint_dict and kepoint_dict[5]["x,y"] != (0, 0):
                ls_coordinates = kepoint_dict[5]["x,y"]
            else:
                pass


            if 6 in kepoint_dict and kepoint_dict[6]["x,y"] != (0, 0):
                rs_coordinates = kepoint_dict[6]["x,y"]
            else:
                pass
            
            now_time = time.time()
            if now_time - first_time >= 0.2:
                first_time = time.time()
                if 0 in kepoint_dict and kepoint_dict[0]["x,y"] != (0, 0):
                    if 10 in kepoint_dict and kepoint_dict[10]["x,y"] != (0, 0) and 9 in kepoint_dict and kepoint_dict[9]["x,y"] != (0, 0):
                        if lw_coordinates[1] < nose_coordinates[1] and rw_coordinates[1] < nose_coordinates[1] and lw_coordinates[0] > ls_coordinates[0] and rw_coordinates[0] < rs_coordinates[0]:
                            if count == 0 :
                                maintime = time.time()
                                count += 1
                                #print(count)#카운트가 나오는지확인하기위한 출력
                            else:
                                count +=1
                                #print(count)
                else:      
                    pass
            else:
                pass
            if maintime is not None:
                if now_time - maintime >= 3:
                    if count >= 10:
                        print("help!!!!!")
                        count = 0
                    else:
                        count = 0
            
            

            

    else:
        pass

    cv2.imshow('YOLOv Pose Estimation', annotated_frame)

    # 'q' 키를 누르면 종료
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
cap.release()
cv2.destroyAllWindows()
