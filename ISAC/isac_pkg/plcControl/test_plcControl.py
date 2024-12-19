from plcControl import ISAC_PLCController


# 외부 신호를 받아 bool 값을 반환하는 함수
def get_external_signal():
    user_input = input("Enter 0 to return True, 1 to return False (or 'exit' to quit): ").strip()
    if user_input == '0':
        return True
    elif user_input == '1':
        return False
    elif user_input.lower() == 'exit':
        exit()
    else:
        print("Invalid input. Please enter 0, 1, or 'exit'.")
        return get_external_signal()  # 재귀 호출로 올바른 입력을 받을 때까지 반복


# PLCController 인스턴스 생성
plc_controller = ISAC_PLCController('192.168.0.70', 0, 1, 1)  # IP 주소, 랙, 슬롯, DB 번호
try:
    while True:
        external_signal = get_external_signal()  # 외부 신호 값을 받아옴
        
        if external_signal == True:
            plc_controller.controlBit(0, True)
            plc_controller.controlBit(0, False)  # 0.5초 후 비트 끄기
        elif external_signal == False:
            plc_controller.controlBit(1, True)
            plc_controller.controlBit(1, False)  # 0.5초 후 비트 끄기
finally:
    plc_controller.disconnect()


