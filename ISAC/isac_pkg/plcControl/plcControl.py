import snap7
from snap7.util import *
import time

class ISAC_PLCController:
    def __init__(self, ip_address, rack, slot, db_number):
        """
        초기화 함수
        Input:
            - ip_address: PLC의 IP 주소 (str)
            - rack: PLC의 랙 번호 (int)
            - slot: PLC의 슬롯 번호 (int)
            - db_number: 데이터 블록(DB) 번호 (int)
        """
        self.plc = snap7.client.Client()
        self.plc.connect(ip_address, rack, slot)
        self.db_number = db_number

    def read_data(self, start, size):
        """
        데이터 읽기 함수
        Input:
            - start: 읽기 시작 위치 (int)
            - size: 읽을 데이터 크기 (int)
        Return:
            - result: 읽은 데이터 (bytearray)
        """
        result = self.plc.db_read(self.db_number, start, size)
        return result

    def write_data(self, start, data):
        """
        데이터 쓰기 함수
        Input:
            - start: 쓰기 시작 위치 (int)
            - data: 쓸 데이터 (bytearray)
        """
        self.plc.db_write(self.db_number, start, data)

    def controlBit(self, bit_position, state):
        """
        비트 제어 함수
        Input:
            - bit_position: 제어할 비트 위치 (int)
            - state: 비트의 상태 (True는 켜짐, False는 꺼짐) (bool)
        """
        if state:
            # 비트 켜기
            data_to_write = bytearray([1 << bit_position])
            self.write_data(0, data_to_write)
            print(f'Bit {bit_position} On')
        else:
            # 비트 끄기
            data_to_write = bytearray([0])
            self.write_data(0, data_to_write)
            print(f'Bit {bit_position} Off')

        # 0.5초 대기
        time.sleep(0.5)

    def disconnect(self):
        self.plc.disconnect()
