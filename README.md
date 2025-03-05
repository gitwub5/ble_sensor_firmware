# Pico2W BLE Sensor Logger

## 📌 프로젝트 개요
이 프로젝트는 **Raspberry Pi Pico W**에서 **BLE(Bluetooth Low Energy) 통신**을 활용하여 센서 데이터를 수집하고 CSV 파일에 기록하는 마이크로파이썬 기반 펌웨어입니다. BLE를 통해 데이터를 송수신하며, UART 프로토콜을 활용한 BLE 통신이 구현되었습니다.

### 🔹 주요 기능
- **센서 데이터 로깅**: 온도 및 습도(DHT20), CPU 온도를 측정하여 CSV 파일로 저장
- **UART 기반 BLE 통신**: BLE Peripheral로 동작하며, BLE를 통해 데이터를 JSON 형식으로 송수신
- **BLE 광고**: 주기적으로 BLE 광고를 실행하여 장치 검색 가능
- **RTC(Real-Time Clock) 동기화**: BLE를 통해 시간 설정 및 관리

## 📂 프로젝트 구조
```plaintext
pico2w_ble_sensor_logger/
├── ble_advertising.py   # BLE 광고 패킷 생성
├── ble_manager.py       # BLE 통신 및 데이터 송수신
├── ble_peripheral.py    # BLE Peripheral 설정 및 관리
├── config.py            # 설정 파일 (기본값, BLE 설정, 핀 번호 등)
├── data_processor.py    # 센서 데이터 수집 및 CSV 저장
├── dht20.py             # DHT20 센서 드라이버
└── main.py              # 메인 루프 (BLE 초기화 및 센서 데이터 로깅)
```

## 📜 파일 설명

### 1️⃣ `main.py` (메인 루프)
- BLE 및 센서 로깅을 관리하는 메인 실행 파일
- **RTC 시간 설정 및 변환**
- **BLE 명령 처리**: 시간 동기화 및 센서 로깅 시작

- **센서 데이터 로깅**: 주기마다 센서 데이터를 파일에 기록

### 2️⃣ `ble_advertising.py` (BLE 광고)
- BLE 광고 패킷을 생성하는 유틸리티 함수 포함

### 3️⃣ `ble_manager.py` (BLE 관리)
- BLE Peripheral 설정 및 연결 관리
- UART를 이용하여 BLE 데이터 송수신
- CSV 데이터 BLE 전송 기능 포함

### 4️⃣ `ble_peripheral.py` (BLE Peripheral 설정)
- **BLE 서비스 및 특성(UUID) 설정**
- **BLE 연결 이벤트 관리**
- **BLE 데이터 송수신 처리**

### 5️⃣ `config.py` (설정 파일)
- **BLE 기본 설정** (디바이스 이름, 광고 주기 등)
- **센서 로깅 설정** (CSV 파일명, 데이터 헤더 등)
- **I2C 핀 번호 설정** (DHT20 센서 연결용)

### 6️⃣ `data_processor.py` (데이터 로깅 및 센서 데이터 처리)
- DHT20 및 CPU 온도 데이터를 측정 후 CSV 파일에 저장
- 센서 데이터 포맷팅 및 파일 관리
- **CSV 데이터 BLE 전송 기능** 포함

### 7️⃣ `dht20.py` (DHT20 센서 드라이버)
- I2C를 이용한 DHT20 온습도 센서 제어
- CRC 검사 및 데이터 변환 포함

## 🔄 주요 로직 설명

### 🟢 1. 메인 루프 (`main.py`)
1. **BLE 초기화** (`BLEManager` 객체 생성)
2. **RTC 시간 설정 및 변환**
3. **BLE 명령 수신 및 처리**
4. **센서 데이터 로깅** (주기마다 `SensorLogger`를 통해 CSV에 저장)

### 🔵 2. BLE 통신 (`ble_manager.py`, `ble_peripheral.py`)
- **BLE Peripheral 동작**: UUID 기반으로 TX(송신), RX(수신) 특성 설정
- **BLE 광고 및 연결 관리** : 연결 및 연결 해제 이벤트 관리 (해제 시 재광고)
- **CSV 데이터 전송 기능**:  BLE를 통해 CSV 데이터를 JSON 형식으로 전송 가능

### 🟠 3. 센서 데이터 처리 (`data_processor.py`)
- **DHT20 센서에서 온습도 데이터 수집**
- **ADC를 이용하여 CPU 온도 측정**
- **CSV 파일 관리 (데이터 저장, 삭제, 로드 등)**

## 🚀 실행 방법
1. **Raspberry Pi Pico W**에 마이크로파이썬을 플래시합니다.
2. 프로젝트 파일을 **Pico W 내부에 업로드**합니다.
3. `main.py` 실행:
   ```python
   import main
   main.main()
   ```
4. BLE를 이용해 디바이스에 연결하고 센서 데이터를 수집합니다.

---
✅ **문의**: 프로젝트 관련 문의는 ssgwoo@gmail.com을 통해 가능합니다.

