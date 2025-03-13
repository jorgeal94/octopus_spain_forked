"""Constants for Octopus Energy Spain."""

DOMAIN = "octopus_spain"

CONF_EMAIL = 'email'
CONF_PASSWORD = 'password'

UPDATE_INTERVAL = 1 # Hours

INTELLIGENT_CHARGE_TIMES: Final = [f"{hour:02}:{mins:02}" for hour in range(4, 12) for mins in INTELLIGENT_MINS_PAST_HOURS][:-1]
INTELLIGENT_SOC_OPTIONS: Final = list(range(10, 105, 5))