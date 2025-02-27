# main.py
import bluetooth
import utime
from ble_manager import BLEManager
from dataprocessor import SensorLogger
import config
import machine

# RTC 초기화
rtc = machine.RTC()

# ------------------------- [RTC 관련 함수] -------------------------
def set_rtc_time(time_str):
    """'YYYY-MM-DD HH:MM:SS' 형식의 문자열을 RTC에 설정"""
    try:
        year, month, day, hour, minute, second = map(int, time_str.replace("-", " ").replace("T", " ").replace(":", " ").split())
        rtc.datetime((year, month, day, 0, hour, minute, second, 0))  # 요일은 0, 마이크로초는 0
        print(f"✅ RTC 설정 완료: {time_str}")
    except Exception as e:
        print(f"❌ RTC 설정 오류: {e}")

def get_rtc_time():
    """현재 RTC 시간을 'YYYY-MM-DDTHH:MM:SS' 형식으로 반환"""
    year, month, day, _, hour, minute, second, _ = rtc.datetime()
    return "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}".format(year, month, day, hour, minute, second)

# ------------------------- [시간 변환 함수] -------------------------
def convert_to_epoch(start_time):
    """Converts 'YYYY-MM-DD HH:MM:SS' format to an epoch timestamp."""
    try:
        year, month, day, hour, minute, second = map(int, start_time.replace("-", " ").replace("T", " ").replace(":", " ").split())
        return utime.mktime((year, month, day, hour, minute, second, 0, 0))
    except Exception as e:
        print(f"Error converting start_time: {e}")
        return None

def convert_period_to_seconds(period):
    """Converts a time interval string to total seconds."""
    try:
        parts = list(map(int, period.split(":")))
        if len(parts) == 3:
            hours, minutes, seconds = parts
        elif len(parts) == 2:
            hours, minutes, seconds = 0, parts[0], parts[1]
        elif len(parts) == 1:
            hours, minutes, seconds = 0, 0, parts[0]
        else:
            raise ValueError("Invalid period format. Use 'H:M:S', 'M:S', or 'S'.")
        return (hours * 3600) + (minutes * 60) + seconds
    except Exception as e:
        print(f"Error converting period: {e}")
        return None

# ------------------------- [BLE 명령 처리] -------------------------
def process_ble_command(ble_manager, sensor_logger, period_seconds):
    if ble_manager.command:
        start_time = ble_manager.latest_time
        period = ble_manager.period

        set_rtc_time(start_time)

        if sensor_logger is None:
            sensor_logger = SensorLogger(start_time, period)
        else:
            sensor_logger.start_time = start_time
            sensor_logger.period = period

        new_period_seconds = convert_period_to_seconds(period)

        ble_manager.command = None
        return sensor_logger, new_period_seconds 
    
    return sensor_logger, period_seconds

# ------------------------- [BLE 광고 상태 확인] -------------------------
def check_ble_advertising(ble_manager, last_advertising_check, current_time):
    """연결이 끊어진 경우 BLE 광고를 다시 시작"""
    if utime.ticks_diff(current_time, last_advertising_check) >= config.ADVERTISING_CHECK_INTERVAL_MS:
        if ble_manager.sp and not ble_manager.sp.is_connected():
            ble_manager.start_advertising()
            print("🔄 Connection lost, restarting BLE advertising...")
        return utime.ticks_ms()
    return last_advertising_check

# ------------------------- [센서 데이터 로깅] -------------------------
def log_sensor_data(sensor_logger, period_seconds, last_logged_time):
    """RTC 시간을 기준으로 주기가 되면 센서 데이터를 로깅"""
    current_time = get_rtc_time()  # 현재 RTC 시간 가져오기
    current_epoch = convert_to_epoch(current_time)  # 현재 시간 epoch 변환

     # 🔄 마지막으로 로그를 남긴 시간이 같은 경우, 중복 로깅 방지
    if current_epoch == last_logged_time:
        return last_logged_time

    if last_logged_time is None or (current_epoch - last_logged_time) >= period_seconds:
        sensor_logger.get_sensor_log(current_time)
        print(f"📌 {current_time} - 센서 데이터 로깅됨!")
        return current_epoch  # 마지막 로깅 시간 업데이트
    
    return last_logged_time  # 업데이트 없음

# ------------------------- [메인 루프] -------------------------
def main():
    #ble 초기화
    ble = bluetooth.BLE()
    ble_manager = BLEManager(ble)

    # 시간 변수 초기화
    last_advertising_check = utime.ticks_ms()
    sensor_logger = None
    period_seconds = None
    last_logged_time = None

    while True:
        current_time = utime.ticks_ms()

        # 1️⃣ BLE 광고 상태 확인 (연결이 끊어졌다면 광고 시작)
        last_advertising_check = check_ble_advertising(ble_manager, last_advertising_check, current_time)

        # 2️⃣ BLE 명령 처리 (새로운 데이터 로깅 시작)
        sensor_logger, period_seconds = process_ble_command(ble_manager, sensor_logger, period_seconds)

        # 3️⃣ 주기마다 센서 데이터 로깅 실행
        if sensor_logger is not None and period_seconds is not None:
            last_logged_time = log_sensor_data(sensor_logger, period_seconds, last_logged_time)

        # 1초 대기
        utime.sleep_ms(1000)

if __name__ == "__main__":
    main()
