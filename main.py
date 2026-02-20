import os
import json
import asyncio
import logging
import requests
from fastapi import FastAPI
from azure.iot.device import IoTHubDeviceClient, Message
from dotenv import load_dotenv

# =====================================================
# LOAD ENV
# =====================================================
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SEND_INTERVAL_SEC = int(os.getenv("SEND_INTERVAL_SEC", 60))
WEATHER_URL = "https://weather.googleapis.com/v1/currentConditions:lookup"

LOCATIONS_JSON = os.getenv("LOCATIONS_JSON")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not set")

if not LOCATIONS_JSON:
    raise ValueError("LOCATIONS_JSON not set")

LOCATIONS = json.loads(LOCATIONS_JSON)

# =====================================================
# LOGGING CONFIG
# =====================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

# =====================================================
# FASTAPI
# =====================================================
app = FastAPI()
device_clients = {}

# =====================================================
# GOOGLE WEATHER
# =====================================================
def get_current_weather(latitude: float, longitude: float):
    params = {
        "key": GOOGLE_API_KEY,
        "location.latitude": latitude,
        "location.longitude": longitude
    }

    try:
        response = requests.get(WEATHER_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        humidity = data.get("relativeHumidity")
        if isinstance(humidity, dict):
            humidity = humidity.get("percent")

        return {
            "timestamp": data.get("currentTime"),
            "temperature_c": data.get("temperature", {}).get("degrees"),
            "humidity_percent": humidity,
            "uv_index": data.get("uvIndex")
        }

    except Exception as e:
        logger.error(f"Weather API error: {e}")
        return None

# =====================================================
# SEND TELEMETRY
# =====================================================
def send_telemetry(client, payload: dict):
    message = Message(json.dumps(payload))
    message.content_encoding = "utf-8"
    message.content_type = "application/json"
    client.send_message(message)

# =====================================================
# BACKGROUND LOOP
# =====================================================
async def telemetry_loop():
    logger.info("Telemetry background loop started")

    while True:
        for loc in LOCATIONS:
            location_id = loc["location_id"]
            client = device_clients.get(location_id)

            if not client:
                logger.warning(f"[{location_id}] Device client not available")
                continue

            weather = get_current_weather(
                loc["latitude"],
                loc["longitude"]
            )

            if not weather:
                logger.warning(f"[{location_id}] Weather data unavailable")
                continue

            telemetry = {
                "locationId": location_id,
                "timestamp": weather["timestamp"],
                "temp": weather["temperature_c"],
                "humi": weather["humidity_percent"],
                "uv_index": weather["uv_index"]
            }

            try:
                send_telemetry(client, telemetry)
                logger.info(f"[{location_id}] Telemetry sent successfully")

            except Exception as e:
                logger.error(f"[{location_id}] Send telemetry failed: {e}")

        await asyncio.sleep(SEND_INTERVAL_SEC)

# =====================================================
# STARTUP EVENT
# =====================================================

@app.on_event("startup")
async def startup_event():

    logger.info("Starting Weather Telemetry Service...")

    for loc in LOCATIONS:
        location_id = loc["location_id"]
        env_key = f"IOT_CONN_{location_id.upper().replace('-', '_')}"
        conn_str = os.getenv(env_key)

        if not conn_str:
            logger.error(f"[{location_id}] Connection string not found in ENV ({env_key})")
            continue

        try:
            client = IoTHubDeviceClient.create_from_connection_string(conn_str)
            client.connect()
            device_clients[location_id] = client

            logger.info(f"[{location_id}] Connected to IoT Hub successfully")

        except Exception as e:
            logger.error(f"[{location_id}] IoT Hub connection failed: {e}")

    asyncio.create_task(telemetry_loop())

@app.get("/")
def root():
    return {"message": "Weather Telemetry Service is running"}
# =====================================================
# SHUTDOWN EVENT
# =====================================================
@app.on_event("shutdown")
def shutdown_event():
    logger.info("Shutting down service...")

    for location_id, client in device_clients.items():
        try:
            client.disconnect()
            logger.info(f"[{location_id}] Disconnected successfully")
        except Exception as e:
            logger.error(f"[{location_id}] Disconnect failed: {e}")

# =====================================================
# ROUTES
# =====================================================
@app.get("/health")
def health():
    return {
        "status": "running",
        "connected_devices": list(device_clients.keys())
    }

@app.get("/devices")
def devices():
    return {
        "devices": list(device_clients.keys())
    }
