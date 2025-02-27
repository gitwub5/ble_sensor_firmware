# config.py
import machine

# BLE 기본 설정
raw_uid = machine.unique_id()
DEVICE_UID = "".join("{:02X}".format(b) for b in raw_uid)
DEVICE_NAME = "MedM" + DEVICE_UID[-4:]

NAME_FILE = "name.txt"
DATA_FILE = "sensor_data.csv"
DATA_HEADER = ["time", "tp", "hd", "cputp"]  # UID 제거

# 기본 로깅 설정
DEFAULT_START_TIME = "2025-01-01 00:00:00"
DEFAULT_PERIOD = "01:00:00"

# BLE 광고 관련 설정
ADVERTISE_INTERVAL = 10 * 100000 # 10초 인터벌
ADVERTISING_CHECK_INTERVAL_MS = 60 * 1000  # 1분마다 BLE 광고 유지 확인 (밀리초)
BLE_CHUNK_SIZE = 10  # BLE 데이터 전송 시 한 번에 보낼 줄 수

I2C_SCL_PIN = 21  # SCL 핀 번호
I2C_SDA_PIN = 20  # SDA 핀 번호
