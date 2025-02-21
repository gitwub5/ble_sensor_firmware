# main.py
import bluetooth
import utime
from ble_manager import BLEManager
from dataprocessor import SensorLogger
import config

# ------------------------- [BLE 초기화] -------------------------
def init_ble():
    """BLE 초기화 및 광고 시작"""
    ble = bluetooth.BLE()
    ble_manager = BLEManager(ble)
    ble_manager.start_advertising()
    return ble_manager

# ------------------------- [BLE 명령 처리] -------------------------
def process_ble_command(ble_manager, sensor_logger):
    """BLE 명령을 처리하고, 최신 시간과 주기를 업데이트"""
    if ble_manager.command:
        start_time = ble_manager.latest_time
        period = ble_manager.period

        # SensorLogger 초기화 또는 업데이트
        if sensor_logger is None:
            sensor_logger = SensorLogger(start_time, period)
        else:
            sensor_logger.start_time = start_time
            sensor_logger.period = period

        # 시간 변환
        start_epoch = sensor_logger.convert_to_epoch(start_time)
        period_seconds = sensor_logger.convert_period_to_seconds(period)

        # 센서 데이터 로깅 시작
        time_seq = sensor_logger.start_logging(0, start_epoch, period_seconds)

        # 명령 처리 후 초기화
        ble_manager.command = None
        return sensor_logger, time_seq, start_epoch, period_seconds
    return sensor_logger, None, None, None

# ------------------------- [BLE 광고 상태 확인] -------------------------
def check_ble_advertising(ble_manager, last_advertising_check, current_time):
    """연결이 끊어진 경우 BLE 광고를 다시 시작"""
    if utime.ticks_diff(current_time, last_advertising_check) >= config.ADVERTISING_CHECK_INTERVAL_MS:
        if not ble_manager.sp.is_connected():
            ble_manager.start_advertising()
            print("🔄 Connection lost, restarting BLE advertising...")
        return utime.ticks_ms()  # 광고 체크 시간 갱신
    return last_advertising_check

# ------------------------- [센서 데이터 로깅] -------------------------
def log_sensor_data(sensor_logger, last_logging_time, current_time, time_seq, start_epoch, period_seconds):
    """주기마다 센서 데이터를 로깅"""
    if last_logging_time is not None and utime.ticks_diff(current_time, last_logging_time) >= period_seconds * 1000:
        time_seq = sensor_logger.start_logging(time_seq, start_epoch, period_seconds)
        return time_seq, current_time  # 새로운 로그 시간 반환
    return time_seq, last_logging_time

# ------------------------- [메인 루프] -------------------------
def main():
    ble_manager = init_ble()

    # 시간 변수 초기화
    last_advertising_check = utime.ticks_ms()
    last_logging_time = None
    sensor_logger = None
    time_seq = 0
    start_epoch = None
    period_seconds = None

    while True:
        current_time = utime.ticks_ms()

        # 1️⃣ BLE 광고 상태 확인 (연결이 끊어졌다면 광고 시작)
        last_advertising_check = check_ble_advertising(ble_manager, last_advertising_check, current_time)

        # 2️⃣ BLE 명령 처리 (새로운 데이터 로깅 시작)
        sensor_logger, time_seq, start_epoch, period_seconds = process_ble_command(ble_manager, sensor_logger)

        # 3️⃣ 주기마다 센서 데이터 로깅 실행
        if sensor_logger:
            time_seq, last_logging_time = log_sensor_data(sensor_logger, last_logging_time, current_time, time_seq, start_epoch, period_seconds)

        # 1초 대기
        utime.sleep_ms(1000)

if __name__ == "__main__":
    main()
