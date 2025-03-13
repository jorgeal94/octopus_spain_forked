import logging
from datetime import datetime, timedelta

from python_graphql_client import GraphqlClient


GRAPH_QL_ENDPOINT = "https://api.oees-kraken.energy/v1/graphql/"
SOLAR_WALLET_LEDGER = "SOLAR_WALLET_LEDGER"
ELECTRICITY_LEDGER = "SPAIN_ELECTRICITY_LEDGER"

_LOGGER = logging.getLogger(__name__)

class OctopusSpain:
    def __init__(self, email, password):
        self._email = email
        self._password = password
        self._token = None

    async def login(self):
        mutation = """
           mutation obtainKrakenToken($input: ObtainJSONWebTokenInput!) {
              obtainKrakenToken(input: $input) {
                token
              }
            }
        """
        variables = {"input": {"email": self._email, "password": self._password}}

        client = GraphqlClient(endpoint=GRAPH_QL_ENDPOINT)
        response = await client.execute_async(mutation, variables)

        if "errors" in response:
            return False

        self._token = response["data"]["obtainKrakenToken"]["token"]
        return True

    async def accounts(self):
        query = """
             query getAccountNames{
                viewer {
                    accounts {
                        ... on Account {
                            number
                        }
                    }
                }
            }
            """

        headers = {"authorization": self._token}
        client = GraphqlClient(endpoint=GRAPH_QL_ENDPOINT, headers=headers)
        response = await client.execute_async(query)

        return list(map(lambda a: a["number"], response["data"]["viewer"]["accounts"]))

    async def account(self, account: str):
        query = """
            query ($account: String!) {
              accountBillingInfo(accountNumber: $account) {
                ledgers {
                  ledgerType
                  statementsWithDetails(first: 1) {
                    edges {
                      node {
                        amount
                        consumptionStartDate
                        consumptionEndDate
                        issuedDate
                      }
                    }
                  }
                  balance
                }
              }
            }
        """
        headers = {"authorization": self._token}
        client = GraphqlClient(endpoint=GRAPH_QL_ENDPOINT, headers=headers)
        response = await client.execute_async(query, {"account": account})
        ledgers = response["data"]["accountBillingInfo"]["ledgers"]
        electricity = next(filter(lambda x: x['ledgerType'] == ELECTRICITY_LEDGER, ledgers), None)
        solar_wallet = next(filter(lambda x: x['ledgerType'] == SOLAR_WALLET_LEDGER, ledgers), {'balance': 0})

        if not electricity:
            raise Exception("Electricity ledger not found")

        invoices = electricity["statementsWithDetails"]["edges"]

        if len(invoices) == 0:
            return {
                'solar_wallet': None,
                'last_invoice': {
                    'amount': None,
                    'issued': None,
                    'start': None,
                    'end': None
                }
            }

        invoice = invoices[0]["node"]

        # Los timedelta son bastante chapuzas, habrá que arreglarlo
        return {
            "solar_wallet": (float(solar_wallet["balance"]) / 100),
            "octopus_credit": (float(electricity["balance"]) / 100),
            "last_invoice": {
                "amount": invoice["amount"] if invoice["amount"] else 0,
                "issued": datetime.fromisoformat(invoice["issuedDate"]).date(),
                "start": (datetime.fromisoformat(invoice["consumptionStartDate"]) + timedelta(hours=2)).date(),
                "end": (datetime.fromisoformat(invoice["consumptionEndDate"]) - timedelta(seconds=1)).date(),
            },
        }
    
    async def registered_krakenflex_device(self, account_number: str):
        """Consulta los dispositivos registrados en Krakenflex."""
        query = """
        query registeredKrakenflexDevice($accountNumber: String!) {
            registeredKrakenflexDevice(accountNumber: $accountNumber) {
                krakenflexDeviceId
                provider
                vehicleMake
                vehicleModel
                vehicleBatterySizeInKwh
                chargePointMake
                chargePointModel
                chargePointPowerInKw
                status
                suspended
                hasToken
                createdAt
            }
        }
        """
        headers = {"authorization": self._token}
        client = GraphqlClient(endpoint=GRAPH_QL_ENDPOINT, headers=headers)
        response = await client.execute_async(query, {"accountNumber": account_number})

        return response.get("data", {}).get("registeredKrakenflexDevice", None)

    async def get_vehicle_charging_preferences(self, account_number: str):
        """Obtiene las preferencias de carga del vehículo desde la API GraphQL."""
        query = """
        query vehicleChargingPreferences($accountNumber: String!) {
            vehicleChargingPreferences(accountNumber: $accountNumber) {
              weekdayTargetTime,
              weekdayTargetSoc,
              weekendTargetTime,
              weekendTargetSoc
            }
        }
        """
        headers = {"authorization": self._token}
        client = GraphqlClient(endpoint=GRAPH_QL_ENDPOINT, headers=headers)
        response = await client.execute_async(query, {"accountNumber": account_number})
        
        return response.get("data", {}).get("vehicleChargingPreferences", None)

    async def set_target_soc(self, account_id: str, weekday_target_soc: int, weekend_target_soc: int, weekday_target_time: str, weekend_target_time: str):
        """Actualiza las preferencias de carga del vehículo en la API GraphQL."""
        mutation = """
        mutation setVehicleChargePreferences($accountNumber: String!, $weekdayTargetTime: String!, $weekdayTargetSoc: Int!, $weekendTargetTime: String!, $weekendTargetSoc: Int!) {
            setVehicleChargePreferences(
                input: {accountNumber: $accountNumber, weekdayTargetTime: $weekdayTargetTime, weekdayTargetSoc: $weekdayTargetSoc, weekendTargetTime: $weekendTargetTime, weekendTargetSoc: $weekendTargetSoc}
            ) {
                possibleErrors {
                    type
                    message
                    description
                    code
                }
            }
        }
        """
        variables = {
            "accountNumber": account_id,
            "weekdayTargetTime": weekday_target_time,
            "weekdayTargetSoc": weekday_target_soc,
            "weekendTargetTime": weekend_target_time,
            "weekendTargetSoc": weekend_target_soc
        }
    
        client = GraphqlClient(endpoint=GRAPH_QL_ENDPOINT, headers={"authorization": self._token})  # Asegúrate de incluir el token
        response = await client.execute_async(mutation, variables)
    
        # Verificar si hay errores
        possible_errors = response.get("data", {}).get("setVehicleChargePreferences", {}).get("possibleErrors", [])
        if possible_errors:
            for error in possible_errors:
                _LOGGER.error(f"Error al actualizar preferencias de carga: {error.get('message')}")
            return False
    
        return True
    
    