# ble_manager.py
import time
from ble_peripheral import BLEPeripheral
import config
import json

# ==========================================================
# [1] BLEManger 클래스 정의
# ==========================================================
class BLEManager:
    def __init__(self, ble):
        """BLEManager 클래스 초기화"""
        self._ble = ble
        self._ble.active(True)
        
        # 기본 BLE 설정
        self._name = self._load_ble_name()  # 저장된 BLE 이름 불러오기
        self.latest_time = config.DEFAULT_START_TIME  # 기본 최신 시간 설정
        self.period = config.DEFAULT_PERIOD  # 기본 로깅 주기 설정
        self.interval = config.ADVERTISE_INTERVAL 
        self.command = None  # 현재 실행할 명령어
        self.partial_data = ""  # 조각난 데이터 저장 버퍼

        #  BLE 장치 초기화 및 이벤트 핸들러 등록
        self.sp = BLEPeripheral(self._ble, name=self._name, interval = self.interval)
        self.sp.on_write(self.on_rx)
        
        print(f"BLE Started with name: {self._name}")

    # ==========================================================
    # [2] BLE 이름 관리
    # ==========================================================

    def _load_ble_name(self):
        """Flash 메모리에서 BLE 이름 불러오기"""
        try:
            with open(config.NAME_FILE, "r") as f:
                return f.read().strip()
        except OSError:
            return config.DEVICE_NAME

    def set_ble_name(self, new_name):
        """BLE 이름 변경 후 다시 광고 시작"""
        self._name = new_name
        with open(config.NAME_FILE, "w") as f:
            f.write(new_name)

        # BLE 장치 재설정
        self.sp = BLEPeripheral(self._ble, name=self._name, interval= self.interval)
        self.sp.on_write(self.on_rx)

        # BLE 광고를 새로 시작
        self.start_advertising()
        
    # ==========================================================
    # [3] BLE 데이터 수신 및 명령 처리
    # ==========================================================
    
    def on_rx(self, data):
        """BLE 데이터 수신 핸들러 (MTU 제한 고려하여 데이터 조립)"""
        received_chunk = str(data, "utf-8").strip()
        self.partial_data += received_chunk  # 데이터 이어 붙이기
        print(f"Received chunk: {received_chunk}")

        # 완전한 명령어인지 확인 (JSON 객체가 완전한지 체크)
        if "}" in self.partial_data:
            try:
                complete_command = json.loads(self.partial_data)  # JSON 파싱
                self.partial_data = ""  # 버퍼 초기화
                print(f"Complete command received: {complete_command}")

                # 명령어 처리 및 응답 생성
                response = self.process_command(complete_command)

                # 처리 결과를 JSON 형식으로 BLE 응답
                self.sp.send(json.dumps(response))

            except json.JSONDecodeError:
                print("❌ JSON Parsing Error")
                self.sp.send(json.dumps({"status": "error", "message": "Invalid JSON"}))
                self.partial_data = ""  # 오류 발생 시 버퍼 초기화

            status = f"Status -> Time: {self.latest_time}, Period: {self.period}, Name: {self._name}"
            print(status)

    def process_command(self, data):
        """BLE 명령어를 해석하여 설정값을 변경하거나 데이터를 전송"""
        try:
            command = data.get("command")
            latest_time = data.get("latest_time", self.latest_time)
            period = data.get("period", self.period)
            name = data.get("name", None)

            if period is None:
                period = self.period

            if command not in ["setting", "update"]:
                return {"status": "error", "message": "Unknown command"}

            self.command = command
            self.latest_time = latest_time
            self.period = period
            
            if name:  
                self.set_ble_name(name)

            if command == "update":
                success = self.send_csv_data()
                return {"status": "success" if success else "error", "message": "Data update"}
                
            elif command == "setting":
                return {
                    "status": "success",
                    "message": "Settings update",
                    "data": {
                        "latest_time": self.latest_time,
                        "period": self.period,
                        "name": self._name
                    }
                }

        except Exception as e:
            print("error {str(e)}")

            return {"status": "error", "message": str(e)}
    
    # ==========================================================
    # [4] CSV 데이터 전송 및 관리
    # ==========================================================
            
    def send_csv_data(self):
        """CSV 파일을 BLE로 전송"""
        batch_size = config.BLE_CHUNK_SIZE
        header = ""

        try:
            with open(config.DATA_FILE, "r") as file:
                lines = [line.strip() for line in file.readlines()]  # 파일 전체 읽기
                
            if len(lines) <= 1:
                self.sp.send(json.dumps({"status": "success", "message": "No data available"}))
                return True
            
            header = lines[0]  # 헤더 저장
            data_lines = lines[1:]  # 데이터 부분만 추출

            total_batches = (len(data_lines) + batch_size - 1) // batch_size  # 전체 배치 개수 계산
            print(f"📡 Sending {len(data_lines)} lines via BLE in {total_batches} batches...")

            for i in range(0, len(data_lines), batch_size):  # 10줄씩 묶어서 전송
                if not self.sp.is_connected():  # 연결이 끊어지면 중단
                    print("❌ BLE connection lost. Stopping transmission.")
                    return False

                batch_data = data_lines[i:i + batch_size]  # 배치 데이터 추출

                # 🚀 JSON 형태로 데이터 패키징
                json_payload = json.dumps({
                    "batch": {
                        "index": i // batch_size + 1,
                        "total": total_batches
                    },
                    "data": batch_data
                })

                # BLE 전송 시 예외 처리 추가
                try:
                    self.sp.send(json_payload)
                    print(f"✅ Sent batch {i // batch_size + 1} / {total_batches}")
                except Exception as e:
                    print(f"⚠️ BLE send error: {e}")
                    return False

                time.sleep(0.3)

            print("✅ File sent successfully.")
            self.clear_sent_data()

            return True

        except OSError:
            return False

    def clear_sent_data(self):
        """CSV 파일을 완전히 초기화하고, 헤더를 다시 작성"""
        try:
            with open(config.DATA_FILE, "w") as file:
                file.write(",".join(config.DATA_HEADER) + "\n")  # 헤더 저장
            print("🗑️ Sent data cleared, only header remains.")
        except Exception as e:
            print(f"⚠️ Error clearing sent data: {e}")
    
    # ==========================================================
    # [5] BLE 광고 관리
    # ==========================================================

    def start_advertising(self):
        """BLE 광고 시작"""
        if not self.sp.is_connected():  # 연결 중이 아닐 때만 광고 실행
            self.sp._advertise(interval_us = self.interval)
