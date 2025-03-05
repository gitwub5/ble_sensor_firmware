# config.py
import machine

# BLE 기본 설정
raw_uid = machine.unique_id()
DEVICE_UID = "".join("{:02X}".format(b) for b in raw_uid) # HEX 문자열 변환
DEVICE_NAME = "MedM" + DEVICE_UID[-4:]

NAME_FILE = "name.txt"
DATA_FILE = "sensor_data.csv"
DATA_HEADER = ["time", "tp", "hd", "cputp"]  # UID 제거

# 기본 로깅 설정
DEFAULT_START_TIME = "2025-01-01 00:00:00"
DEFAULT_PERIOD = "01:00:00"

# BLE 광고 관련 설정 (https://docs.micropython.org/en/latest/library/bluetooth.html#class-ble)
# 광고 간격: 625μs 단위로 반올림되며, 일반적으로 20ms(20000μs) ~ 10.24s(10240000μs) 사이의 값을 사용합니다.
ADVERTISE_INTERVAL = 5 * 1000000 # 5초 인터벌 (단위 - 마이크로초)
BLE_CHUNK_SIZE = 10  # BLE 데이터 전송 시 한 번에 보낼 줄 수

I2C_SCL_PIN = 21  # SCL 핀 번호
I2C_SDA_PIN = 20  # SDA 핀 번호
