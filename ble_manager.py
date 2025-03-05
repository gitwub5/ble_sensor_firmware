# ble_manager.py
import bluetooth
import time
from ble_peripheral import BLEPeripheral
import config
import json

# ------------------------- [BLEManager Class Definition] -------------------------
class BLEManager:
    def __init__(self):
        """Initialize BLEManager class"""
        ble = bluetooth.BLE()
        self._ble = ble
        
        # Default BLE settings
        self._name = self._load_ble_name()  # Load stored BLE name
        self.latest_time = config.DEFAULT_START_TIME  # Default latest time setting
        self.period = config.DEFAULT_PERIOD  # Default logging period setting
        self.interval = config.ADVERTISE_INTERVAL 
        self.command = None  # Command to execute
        self.partial_data = ""  # Buffer to store fragmented data

        # Initialize BLE device and register event handler
        self.sp = BLEPeripheral(self._ble, self._name, self.interval)
        self.sp.on_write(self.on_rx)
        
        print(f"BLE Started with name: {self._name}")

    # ------------------------- [BLE Name Management] -------------------------
    def _load_ble_name(self):
        """Load BLE name from Flash memory"""
        try:
            with open(config.NAME_FILE, "r") as f:
                return f.read().strip()
        except OSError:
            return config.DEVICE_NAME

    def set_ble_name(self, new_name):
        """Change BLE name and restart advertising"""
        self._name = new_name
        with open(config.NAME_FILE, "w") as f:
            f.write(new_name)

        # Reinitialize BLE device
        self.sp = BLEPeripheral(self._ble, self._name, self.interval)
        self.sp.on_write(self.on_rx)
        
    # ------------------------- [BLE Data Reception and Command Processing] -------------------------
    def on_rx(self, data):
        """BLE Data Reception Handler (Assembling fragmented data due to MTU limit)"""
        received_chunk = str(data, "utf-8").strip()
        self.partial_data += received_chunk  # Append data
        print(f"Received chunk: {received_chunk}")

        # Check if the command is complete (Verify if JSON object is complete)
        if "}" in self.partial_data:
            try:
                complete_command = json.loads(self.partial_data)  # Parse JSON
                self.partial_data = ""  # Reset buffer
                print(f"Complete command received: {complete_command}")

                # Process command and generate response
                response = self.process_command(complete_command)

                # Send response via BLE in JSON format
                self.sp.send(json.dumps(response))

            except json.JSONDecodeError:
                print("❌ JSON Parsing Error")
                self.sp.send(json.dumps({"status": "error", "message": "Invalid JSON"}))
                self.partial_data = ""  # Reset buffer on error

            status = f"Status -> Time: {self.latest_time}, Period: {self.period}, Name: {self._name}"
            print(status)

    def process_command(self, data):
        """Interpret BLE command to modify settings or send data"""
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
    
    # ------------------------- [CSV Data Transmission and Management] -------------------------      
    def send_csv_data(self):
        """Send CSV file via BLE"""
        batch_size = config.BLE_CHUNK_SIZE

        try:
            with open(config.DATA_FILE, "r") as file:
                lines = [line.strip() for line in file.readlines()]  # Read entire file
                
            if len(lines) <= 1:
                self.sp.send(json.dumps({"status": "success", "message": "No data available"}))
                return True
            
            data_lines = lines[1:]  # Extract only data lines

            total_batches = (len(data_lines) + batch_size - 1) // batch_size  # Calculate total batches
            print(f"📡 Sending {len(data_lines)} lines via BLE in {total_batches} batches...")
            
            if not self.sp.is_connected():  # Stop if connection is lost
                    print("❌ BLE connection lost. Stopping transmission.")
                    return False
            
            for i in range(0, len(data_lines), batch_size):  # Send in batches of 10 lines
                batch_data = data_lines[i:i + batch_size]  # Extract batch data

                # 🚀 Package data in JSON format
                json_payload = json.dumps({
                    "batch": {
                        "index": i // batch_size + 1,
                        "total": total_batches
                    },
                    "data": batch_data
                })

                # Exception handling for BLE transmission
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
        """Clear CSV file completely and rewrite header"""
        try:
            with open(config.DATA_FILE, "w") as file:
                file.write(",".join(config.DATA_HEADER) + "\n")  # Store header
            print("🗑️ Sent data cleared, only header remains.")
        except Exception as e:
            print(f"⚠️ Error clearing sent data: {e}")
    