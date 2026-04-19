"""Constants for Soehnle Airfresh Clean Connect 500."""

DOMAIN = "soehnle_ac500"

# BLE UUIDs
UUID_WRITE   = "0000EF01-0000-1000-8000-00805F9B34FB"
UUID_EF02    = "0000EF02-0000-1000-8000-00805F9B34FB"
UUID_EF03    = "0000EF03-0000-1000-8000-00805F9B34FB"
UUID_EF04    = "0000EF04-0000-1000-8000-00805F9B34FB"

# ── EF02 Frame Layout ──────────────────────────────────────────────────────
# aa 0d a0 21 | p0  00  p2  00  p4  00  p6  10 e0 02 p10  p11 | ee
#               spd     flg     aqi     adc              adc  chk
#
# p[0]  = fan speed   : 0x00=Speed1, 0x01=Speed2, 0x02=Speed3, 0x03=Speed4
# p[2]  = status flags: see FLAG_* below
# p[4]  = AQI sensor  : 0-255 (PM2.5 / air quality index)
# p[6]  = ADC noise   : ignore
# p[10] = ADC noise   : ignore
# p[11] = checksum    : (p0+p2+p4+p6+p10+0xC0) & 0xFF

# Status flag bits (byte p[2])
FLAG_POWER      = 0x01   # Bit 0
FLAG_UVC        = 0x02   # Bit 1
FLAG_NIGHT      = 0xC0   # Bit 6+7 (both always together)
FLAG_AUTO       = 0x20   # Bit 5

# Fan speed map  (EF02 p[0] value → preset name)
SPEED_MAP = {0: "speed_1", 1: "speed_2", 2: "speed_3", 3: "speed_4"}
SPEED_MAP_INV = {v: k for k, v in SPEED_MAP.items()}

PRESET_MODES = ["speed_1", "speed_2", "speed_3", "speed_4", "auto"]

# Write commands
COMMANDS = {
    "power_on":   "aa0301000105ee",
    "power_off":  "aa0301000004ee",
    "uvc_on":     "aa0303000107ee",
    "uvc_off":    "aa0303000006ee",
    "night_on":   "aa030600010aee",
    "night_off":  "aa03af0001b3ee",
    "speed_1":    "aa0302000005ee",
    "speed_2":    "aa0302000106ee",
    "speed_3":    "aa0302000207ee",
    "speed_4":    "aa0302000308ee",
    "auto_on":    "aa0305000109ee",
    "auto_off":   "aa0305000008ee",
}
