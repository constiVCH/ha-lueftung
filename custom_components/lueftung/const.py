"""Konstanten für die Lüftungssteuerung."""

DOMAIN = "lueftung"
API_BASE_URL = "https://api.sec-smart.app/v1"

CONF_DEVICE_ID = "device_id"
CONF_API_TOKEN = "api_token"
CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_SCAN_INTERVAL = 120

LUEFTUNG_MODES = [
    "Fans off",
    "Manual 1",
    "Manual 2",
    "Manual 3",
    "Manual 4",
    "Manual 5",
    "Manual 6",
    "Boost ventilation",
    "Humidity regulation",
    "CO2 regulation",
    "Timed program",
    "Snooze",
    "INACTIVE",
]

MANUAL_MODES = ["Manual 1", "Manual 2", "Manual 3", "Manual 4", "Manual 5", "Manual 6"]

NUM_AREAS = 6

STORAGE_KEY = f"{DOMAIN}.rules"
STORAGE_VERSION = 1

CONF_TEMP_RULES = "temp_rules"
CONF_HUMIDITY_RULES = "humidity_rules"
CONF_NIGHT_MODE = "night_mode"

RULE_NAME = "name"
RULE_SENSOR = "sensor"
RULE_AREAS = "areas"
RULE_THRESHOLD = "threshold"
RULE_CONDITION = "condition"
RULE_MODE = "mode"
RULE_ENABLED = "enabled"

NIGHT_START = "start"
NIGHT_END = "end"
NIGHT_AREAS = "areas"
NIGHT_MODE = "mode"
NIGHT_ENABLED = "enabled"
