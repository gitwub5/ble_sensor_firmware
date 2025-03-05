# main.py
import utime
from ble_manager import BLEManager
from data_processor import SensorLogger
import machine

# RTC initialization
rtc = machine.RTC()

# ------------------------- [RTC Functions] -------------------------
def set_rtc_time(time_str):
    """Set RTC with a time string in 'YYYY-MM-DD HH:MM:SS' format"""
    try:
        year, month, day, hour, minute, second = map(int, time_str.replace("-", " ").replace("T", " ").replace(":", " ").split())
        rtc.datetime((year, month, day, 0, hour, minute, second, 0))  # Day of the week is 0, microseconds are 0
        print(f"✅ RTC set successfully: {time_str}")
    except Exception as e:
        print(f"❌ RTC setting error: {e}")

def get_rtc_time():
    """Return the current RTC time in 'YYYY-MM-DDTHH:MM:SS' format"""
    year, month, day, _, hour, minute, second, _ = rtc.datetime()
    return "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}".format(year, month, day, hour, minute, second)

# ------------------------- [Time Conversion Functions] -------------------------
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

# ------------------------- [BLE Command Processing] -------------------------
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

# ------------------------- [Sensor Data Logging] -------------------------
def log_sensor_data(sensor_logger, period_seconds, last_logged_time):
    """Log sensor data at defined intervals based on RTC time"""
    current_time = get_rtc_time()  # Get current RTC time
    current_epoch = convert_to_epoch(current_time)  # Convert current time to epoch

    # Prevent duplicate logging if the last logged time is the same
    if current_epoch == last_logged_time:
        return last_logged_time

    if last_logged_time is None or (current_epoch - last_logged_time) >= period_seconds:
        sensor_logger.get_sensor_log(current_time)
        print(f"📌 {current_time} - Sensor data logged!")
        return current_epoch  # Update last logged time
    
    return last_logged_time  # No update

# ------------------------- [Main Loop] -------------------------
def main():
    # Initialize BLE
    ble_manager = BLEManager()

    # Initialize time-related variables
    sensor_logger = None
    period_seconds = None
    last_logged_time = None

    while True:
        # 1. Process BLE commands (start new data logging)
        sensor_logger, period_seconds = process_ble_command(ble_manager, sensor_logger, period_seconds)

        # 2. Execute sensor data logging at regular intervals
        if sensor_logger is not None and period_seconds is not None:
            last_logged_time = log_sensor_data(sensor_logger, period_seconds, last_logged_time)

        # Wait for 1 second
        utime.sleep_ms(1000)

if __name__ == "__main__":
    main()
