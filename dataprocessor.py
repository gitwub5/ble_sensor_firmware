# dataprocessor.py
import machine
import utime
import os
from dht20 import DHT20  # DHT20 라이브러리 사용
import config
    
class SensorLogger:
    """Class to handle temperature, humidity, and material resistivity logging."""

    # ------------------------- Constants -------------------------
    FILENAME = "sensor_data.csv"
    DATA_HEADER = ["Number", "Time", "Temperature", "Humidity", "CPU Temperature"]  # UID 제거

    # ------------------------- Initialization -------------------------
    def __init__(self, start_time, period, dht_pin=28, adc_channel=4):
        # DHT20 초기화 (I2C 사용)
        self.i2c = machine.I2C(0, scl=machine.Pin(config.I2C_SCL_PIN), sda=machine.Pin(config.I2C_SDA_PIN), freq=400000)
        self.sensor = DHT20(0x38, self.i2c) 
        self.adc_sensor = machine.ADC(adc_channel)
        self.conversion_factor = 3.3 / 65535
        
         # Load existing data
        self.data = self.load_from_file()
        self.record_number = self.get_last_record_number()
        self.start_time = start_time
        self.period = period

    # ------------------------- File Handling Methods -------------------------
    def save_to_file(self):
        """Save data to a file in CSV format."""
        try:
            with open(self.FILENAME, "w") as file:
                for row in self.data:
                    file.write(",".join(map(str, row)) + "\n")
        except Exception as e:
            print(f"Error saving file {self.FILENAME}: {e}")

    def load_from_file(self):
        """Load existing data from a CSV file."""
        if self.FILENAME in os.listdir():
            try:
                with open(self.FILENAME, "r") as file:
                    lines = file.readlines()
                    return [line.strip().split(",") for line in lines]
            except Exception as e:
                print(f"Error loading file {self.FILENAME}: {e}")
        return [self.DATA_HEADER]

    def get_last_record_number(self):
        """Determine the last record number from existing data."""
        if len(self.data) > 1:
            try:
                return int(self.data[-1][0]) + 1
            except ValueError:
                print("Error: Invalid data format in CSV file. Resetting data.")
                self.data = [self.DATA_HEADER]
        return 1
    
    def delete_file(self):
        """CSV 파일에서 헤더만 남기고 모든 데이터를 삭제"""
        if self.FILENAME in os.listdir():
            try:
                with open(self.FILENAME, "r") as file:
                    lines = file.readlines()
                
                if lines:
                    header = lines[0]
                else:
                    print("No data found to delete.")
                    return
                
                # Write back the last line
                with open(self.FILENAME, "w") as file:
                    file.write(header)  # 헤더만 다시 저장
                
                print(f"Deleted all data except header in {self.FILENAME}.")

            except Exception as e:
                print(f"Error processing {self.FILENAME}: {e}")
        else:
            print(f"{self.FILENAME} does not exist.")


    # ------------------------- Utility Methods -------------------------
    def generate_uid(self):
        """Generates a unique device ID in hexadecimal format."""
        return ''.join('{:02x}'.format(b) for b in machine.unique_id())

    # ------------------------- Time Conversion Methods -------------------------
    def convert_to_epoch(self, start_time):
        """Converts 'YYYY-MM-DD HH:MM:SS' format to an epoch timestamp."""
        try:
            year, month, day, hour, minute, second = map(int, start_time.replace("-", " ").replace("T", " ").replace(":", " ").split())
            return utime.mktime((year, month, day, hour, minute, second, 0, 0))
        except Exception as e:
            print(f"Error converting start_time: {e}")
            return None

    def convert_period_to_seconds(self, period):
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
    def start_logging(self, time_seq, start_epoch, period_seconds):
        """Start logging sensor data."""
        
        utime.sleep(3)  # 데이터 측정 전 대기

        temperature = self.get_temperature()
        humidity = self.get_humidity()
        cpu_temperature = self.get_cpu_temperature() if hasattr(self, "get_cpu_temperature") else 0
        
        current_epoch = start_epoch + (time_seq * period_seconds) + 3
        time_str = self.format_time(current_epoch)
        
        new_record = [self.record_number, time_str, temperature, humidity, cpu_temperature]
        self.data.append(new_record)
        print(f"{new_record}")
        
        self.save_to_file()
        
        self.record_number += 1
        time_seq += 1
        
        return time_seq