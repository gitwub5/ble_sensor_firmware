# dataprocessor.py
import machine
import os
from dht20 import DHT20  # DHT20 라이브러리 사용
import config
import utime
    
class SensorLogger:
    """Class to handle temperature, humidity, and material resistivity logging."""
    # ------------------------- Initialization -------------------------
    def __init__(self, start_time, period, dht_pin=28, adc_channel=4):
        # DHT20 초기화 (I2C 사용)
        self.i2c = machine.I2C(0, scl=machine.Pin(config.I2C_SCL_PIN), sda=machine.Pin(config.I2C_SDA_PIN), freq=400000)
        self.sensor = DHT20(0x38, self.i2c) 
        self.adc_sensor = machine.ADC(adc_channel)
        self.conversion_factor = 3.3 / 65535
        
         # Load existing data
        self.create_file_if_not_exists()
        self.data = self.load_from_file()
        self.start_time = start_time
        self.period = period

    # ------------------------- File Handling Methods -------------------------
    def create_file_if_not_exists(self):
        """Check if the CSV file exists, if not create it with headers."""
        if config.DATA_FILE not in os.listdir():
            with open(config.DATA_FILE, "w") as file:
                file.write(",".join(config.DATA_HEADER) + "\n")  # 헤더 추가
            print(f"Created new file: {config.DATA_FILE}")

    def append_to_file(self, record):
        """Append a new record to the CSV file."""
        try:
            with open(config.DATA_FILE, "a") as file:
                file.write(",".join(map(str, record)) + "\n")
        except Exception as e:
            print(f"Error appending to file {config.DATA_FILE}: {e}")

    def load_from_file(self):
        """Load existing data from a CSV file."""
        if config.DATA_FILE in os.listdir():
            try:
                with open(config.DATA_FILE, "r") as file:
                    lines = file.readlines()
                    return [line.strip().split(",") for line in lines]
            except Exception as e:
                print(f"Error loading file {config.DATA_FILE}: {e}")
        return [config.DATA_HEADER]

    # ------------------------- Time Conversion Methods -------------------------
    def format_time(self, epoch_time):
        """Converts an epoch timestamp to 'YYYY-MM-DDTHH:MM:SS' format."""  
        try:
            tm = utime.localtime(epoch_time)
            return "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}".format(*tm[:6])
        except Exception as e:
            print("Error formatting time:", e)
            return ""

    # ------------------------- Sensor Reading Methods -------------------------
    def get_temperature(self):
        """Read temperature from DHT20 sensor."""
        try:
            measurements = self.sensor.measurements
            if measurements["crc_ok"]:
                return round(measurements["t"], 2)  # 온도 값 (소수점 2자리)
            else:
                print("Warning: Invalid CRC from DHT20 sensor.")
                return None
        except Exception as e:
            print(f"Error reading temperature: {e}")
            return None

    def get_humidity(self):
        """Read humidity from DHT20 sensor."""
        try:
            measurements = self.sensor.measurements
            if measurements["crc_ok"]:
                return round(measurements["rh"], 2)  # 습도 값 (소수점 2자리)
            else:
                print("Warning: Invalid CRC from DHT20 sensor.")
                return None
        except Exception as e:
            print(f"Error reading humidity: {e}")
            return None

    def get_cpu_temperature(self):
        """Material resistivity를 CPU 온도로 변경 (임시)"""
        try:
            sensor_value = self.adc_sensor.read_u16()
            voltage = sensor_value * self.conversion_factor
            return round(voltage * 100, 2)  # 저항 값으로 변환
        except Exception as e:
            print(f"Error reading CPU temperature: {e}")
            return 0  # 오류 발생 시 기본값 0 반환

    # ------------------------- Data Logging Methods -------------------------
    def get_sensor_log(self, current_time):
        """Start logging sensor data."""
        temperature = self.get_temperature()
        humidity = self.get_humidity()
        cpu_temperature = self.get_cpu_temperature() if hasattr(self, "get_cpu_temperature") else 0
        
        new_record = [current_time, temperature, humidity, cpu_temperature]
        self.append_to_file(new_record)
        print(f"Logged data: {new_record}")