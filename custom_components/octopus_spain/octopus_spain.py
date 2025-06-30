import logging
import aiohttp
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
          _LOGGER.error(f"Error al obtener el token: {response['errors']}")
          return False
      self._token = response["data"]["obtainKrakenToken"]["token"]
      return True

    async def accounts(self):
        query = """
             query getAccountNames {
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
        accounts = list(map(lambda a: a["number"], response["data"]["viewer"]["accounts"]))
        return accounts
    
    async def devices(self, account_number: str):
      """Consulta los dispositivos vinculados a la cuenta en Krakenflex."""
      query = """
      query devices($accountNumber: String!) {
          devices(accountNumber: $accountNumber) {
              id
              name
              deviceType
              ... on SmartFlexVehicle {
                  preferences {
                    schedules {
                      dayOfWeek
                      max
                      time
                    }
                  }
                }
          }
      }
      """
      headers = {"authorization": self._token}
      client = GraphqlClient(endpoint=GRAPH_QL_ENDPOINT, headers=headers)
      response = await client.execute_async(query, {"accountNumber": account_number})
      return response.get("data", {}).get("devices", None)

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
            return {'solar_wallet': None, 'last_invoice': {'amount': None, 'issued': None, 'start': None, 'end': None}}
        invoice = invoices[0]["node"]
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

    async def set_device_preferences(self, device_id: str, mode: str, schedules: list, unit: str):  
      """Configura las preferencias del dispositivo con la nueva mutación GraphQL."""
      if not self._token:
          if not await self.login():
              return {"success": False, "errors": ["No se pudo obtener el token de autenticación."]}

      # --- CAMBIO CLAVE AQUÍ ---
      # Usamos el tipo de entrada correcto que sugiere la API
      mutation = """
      mutation SetDevicePreferences($input: SmartFlexDevicePreferencesInput!) {
        setDevicePreferences(input: $input) {
          __typename
          ... on SmartFlexDevicePreferences {
            id
          }
        }
      }
      """

      variables = {
          "input": {
              "deviceId": device_id,
              "mode": mode,
              "schedules": schedules,
              "unit": unit,
          }
      }
      headers = {"authorization": self._token, "Content-Type": "application/json"}
      client = GraphqlClient(endpoint=GRAPH_QL_ENDPOINT, headers=headers)

      try:
          response = await client.execute_async(mutation, variables)
          if "errors" in response:
              _LOGGER.error(f"❌ Error al establecer preferencias de dispositivo: {response['errors']}")
              return {"success": False, "errors": response["errors"]}
          _LOGGER.info(f"✅ Preferencias del dispositivo actualizadas correctamente: {response}")
          return response.get("data", {}).get("setDevicePreferences", {})
      except aiohttp.ClientError as e:
          _LOGGER.error(f"⚠️ Error de red en set_device_preferences: {e}")
          return {"success": False, "errors": [str(e)]}
    
    async def trigger_boost_charge(self, account_number: str):
        """Activa una carga inmediata (boost)."""
        if not self._token:
            if not await self.login():
                return False

        mutation = """
        mutation triggerBoostCharge($input: TriggerBoostChargeInput!) {
          triggerBoostCharge(input: $input) {
            __typename
          }
        }
        """
        variables = {"input": {"accountNumber": account_number}}
        headers = {"authorization": self._token}
        client = GraphqlClient(endpoint=GRAPH_QL_ENDPOINT, headers=headers)
        
        try:
            response = await client.execute_async(mutation, variables)
            if "errors" in response:
                _LOGGER.error(f"❌ Error al activar la carga inmediata: {response['errors']}")
                return False
            _LOGGER.info(f"✅ Carga inmediata activada con éxito para la cuenta {account_number}")
            return True
        except aiohttp.ClientError as e:
            _LOGGER.error(f"⚠️ Error de red en trigger_boost_charge: {e}")
            return False
            