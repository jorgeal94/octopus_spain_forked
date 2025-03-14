"""Constants for Octopus Energy Spain."""

DOMAIN = "octopus_spain"

CONF_EMAIL = 'email'
CONF_PASSWORD = 'password'

UPDATE_INTERVAL = 1 # Hours

# Opciones para el Target State of Charge (SOC)
INTELLIGENT_SOC_OPTIONS = [
    "20",  # 20%
    "30",  # 30%
    "40",  # 40%
    "50",  # 50%
    "60",  # 60%
    "70",  # 70%
    "80",  # 80%
    "90",  # 90%
    "100"  # 100%
]

# Opciones para el Target Ready By Time (Hora de carga)
INTELLIGENT_CHARGE_TIMES = [
    "06:00",  # 6 AM
    "07:00",  # 7 AM
    "08:00",  # 8 AM
    "09:00",  # 9 AM
    "10:00",  # 10 AM
    "11:00",  # 11 AM
    "12:00",  # 12 PM
    "13:00",  # 1 PM
    "14:00",  # 2 PM
    "15:00",  # 3 PM
    "16:00",  # 4 PM
    "17:00",  # 5 PM
    "18:00",  # 6 PM
    "19:00",  # 7 PM
    "20:00",  # 8 PM
    "21:00"   # 9 PM
]

# Días de la semana (se utilizan para iterar sobre ellos)
DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

