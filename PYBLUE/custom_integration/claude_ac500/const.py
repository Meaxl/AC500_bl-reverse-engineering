"""Constants for Soehnle Airfresh Clean Connect 500."""

DOMAIN = "soehnle_ac500"

# BLE
CHARACTERISTIC_UUID = "0000EF01-0000-1000-8000-00805F9B34FB"

# Fan speed presets
SPEED_OFF   = "off"
SPEED_1     = "speed_1"
SPEED_2     = "speed_2"
SPEED_3     = "speed_3"
SPEED_4     = "speed_4"
SPEED_AUTO  = "auto"

PRESET_MODES = [SPEED_1, SPEED_2, SPEED_3, SPEED_4, SPEED_AUTO]

# BLE commands
COMMANDS = {
    "power_on":       "aa0301000105ee",
    "power_off":      "aa0301000004ee",
    "uvc_on":         "aa0303000107ee",
    "uvc_off":        "aa0303000006ee",
    "night_on":       "aa030600010aee",
    "night_off":      "aa03af0001b3ee",
    "speed_1":        "aa0302000005ee",
    "speed_2":        "aa0302000106ee",
    "speed_3":        "aa0302000207ee",
    "speed_4":        "aa0302000308ee",
    "auto_on":        "aa0305000109ee",
    "auto_off":       "aa0305000008ee",
}
