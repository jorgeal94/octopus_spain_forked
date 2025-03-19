# import logging
# from datetime import datetime, timedelta

# from python_graphql_client import GraphqlClient


# GRAPH_QL_ENDPOINT = "https://api.oees-kraken.energy/v1/graphql/"
# SOLAR_WALLET_LEDGER = "SOLAR_WALLET_LEDGER"
# ELECTRICITY_LEDGER = "SPAIN_ELECTRICITY_LEDGER"

# _LOGGER = logging.getLogger(__name__)

# class OctopusSpain:
#     def __init__(self, email, password):
#         self._email = email
#         self._password = password
#         self._token = None

#     async def login(self):
#         mutation = """
#            mutation obtainKrakenToken($input: ObtainJSONWebTokenInput!) {
#               obtainKrakenToken(input: $input) {
#                 token
#               }
#             }
#         """
#         variables = {"input": {"email": self._email, "password": self._password}}

#         client = GraphqlClient(endpoint=GRAPH_QL_ENDPOINT)
#         response = await client.execute_async(mutation, variables)

#         if "errors" in response:
#             return False

#         self._token = response["data"]["obtainKrakenToken"]["token"]
#         return True

#     async def accounts(self):
#         query = """
#              query getAccountNames{
#                 viewer {
#                     accounts {
#                         ... on Account {
#                             number
#                         }
#                     }
#                 }
#             }
#             """

#         headers = {"authorization": self._token}
#         client = GraphqlClient(endpoint=GRAPH_QL_ENDPOINT, headers=headers)
#         response = await client.execute_async(query)

#         return list(map(lambda a: a["number"], response["data"]["viewer"]["accounts"]))

    # async def account(self, account: str):
    #     query = """
    #         query ($account: String!) {
    #           accountBillingInfo(accountNumber: $account) {
    #             ledgers {
    #               ledgerType
    #               statementsWithDetails(first: 1) {
    #                 edges {
    #                   node {
    #                     amount
    #                     consumptionStartDate
    #                     consumptionEndDate
    #                     issuedDate
    #                   }
    #                 }
    #               }
    #               balance
    #             }
    #           }
    #         }
    #     """
    #     headers = {"authorization": self._token}
    #     client = GraphqlClient(endpoint=GRAPH_QL_ENDPOINT, headers=headers)
    #     response = await client.execute_async(query, {"account": account})
    #     ledgers = response["data"]["accountBillingInfo"]["ledgers"]
    #     electricity = next(filter(lambda x: x['ledgerType'] == ELECTRICITY_LEDGER, ledgers), None)
    #     solar_wallet = next(filter(lambda x: x['ledgerType'] == SOLAR_WALLET_LEDGER, ledgers), {'balance': 0})

    #     if not electricity:
    #         raise Exception("Electricity ledger not found")

    #     invoices = electricity["statementsWithDetails"]["edges"]

    #     if len(invoices) == 0:
    #         return {
    #             'solar_wallet': None,
    #             'last_invoice': {
    #                 'amount': None,
    #                 'issued': None,
    #                 'start': None,
    #                 'end': None
    #             }
    #         }

    #     invoice = invoices[0]["node"]

    #     # Los timedelta son bastante chapuzas, habrá que arreglarlo
    #     return {
    #         "solar_wallet": (float(solar_wallet["balance"]) / 100),
    #         "octopus_credit": (float(electricity["balance"]) / 100),
    #         "last_invoice": {
    #             "amount": invoice["amount"] if invoice["amount"] else 0,
    #             "issued": datetime.fromisoformat(invoice["issuedDate"]).date(),
    #             "start": (datetime.fromisoformat(invoice["consumptionStartDate"]) + timedelta(hours=2)).date(),
    #             "end": (datetime.fromisoformat(invoice["consumptionEndDate"]) - timedelta(seconds=1)).date(),
    #         },
    #     }
    
    # async def registered_krakenflex_device(self, account_number: str):
    #     """Consulta los dispositivos registrados en Krakenflex."""
    #     query = """
    #     query registeredKrakenflexDevice($accountNumber: String!) {
    #         registeredKrakenflexDevice(accountNumber: $accountNumber) {
    #             krakenflexDeviceId
    #             provider
    #             vehicleMake
    #             vehicleModel
    #             vehicleBatterySizeInKwh
    #             chargePointMake
    #             chargePointModel
    #             chargePointPowerInKw
    #             status
    #             suspended
    #             hasToken
    #             createdAt
    #         }
    #     }
    #     """
    #     headers = {"authorization": self._token}
    #     client = GraphqlClient(endpoint=GRAPH_QL_ENDPOINT, headers=headers)
    #     response = await client.execute_async(query, {"accountNumber": account_number})

    #     return response.get("data", {}).get("registeredKrakenflexDevice", None)

    # async def get_vehicle_charging_preferences(self, account_number: str):
    #     """Obtiene las preferencias de carga del vehículo desde la API GraphQL."""
    #     query = """
    #     query vehicleChargingPreferences($accountNumber: String!) {
    #         vehicleChargingPreferences(accountNumber: $accountNumber) {
    #           weekdayTargetTime,
    #           weekdayTargetSoc,
    #           weekendTargetTime,
    #           weekendTargetSoc
    #         }
    #     }
    #     """
    #     headers = {"authorization": self._token}
    #     client = GraphqlClient(endpoint=GRAPH_QL_ENDPOINT, headers=headers)
    #     response = await client.execute_async(query, {"accountNumber": account_number})
        
    #     return response.get("data", {}).get("vehicleChargingPreferences", None)

    # async def set_targets(self, account_id: str, weekday_target_soc: int, weekend_target_soc: int, weekday_target_time: str, weekend_target_time: str):
    #     """Actualiza las preferencias de carga del vehículo en la API GraphQL."""
    #     mutation = """
    #     mutation setVehicleChargePreferences($accountNumber: String!, $weekdayTargetTime: String!, $weekdayTargetSoc: Int!, $weekendTargetTime: String!, $weekendTargetSoc: Int!) {
    #         setVehicleChargePreferences(
    #             input: {accountNumber: $accountNumber, weekdayTargetTime: $weekdayTargetTime, weekdayTargetSoc: $weekdayTargetSoc, weekendTargetTime: $weekendTargetTime, weekendTargetSoc: $weekendTargetSoc}
    #         ) {
    #             possibleErrors {
    #                 type
    #                 message
    #                 description
    #                 code
    #             }
    #         }
    #     }
    #     """
    #     variables = {
    #         "accountNumber": account_id,
    #         "weekdayTargetTime": weekday_target_time,
    #         "weekdayTargetSoc": weekday_target_soc,
    #         "weekendTargetTime": weekend_target_time,
    #         "weekendTargetSoc": weekend_target_soc
    #     }
    
    #     client = GraphqlClient(endpoint=GRAPH_QL_ENDPOINT, headers={"authorization": self._token})  # Asegúrate de incluir el token
    #     response = await client.execute_async(mutation, variables)
    
    #     # Verificar si hay errores
    #     possible_errors = response.get("data", {}).get("setVehicleChargePreferences", {}).get("possibleErrors", [])
    #     if possible_errors:
    #         for error in possible_errors:
    #             _LOGGER.error(f"Error al actualizar preferencias de carga: {error.get('message')}")
    #         return False
    
    #     return True

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
      _LOGGER.info(f"Token obtenido: {self._token}")
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
        _LOGGER.info(f"Cuentas obtenidas: {accounts}")
        return accounts
    
    async def devices(self, account_number: str):
      """Consulta los dispositivos vinculados a la cuenta en Krakenflex."""
      query = """
      query devices($accountNumber: String!) {
          devices(accountNumber: $accountNumber) {
              id
              name
              deviceType
              status {
                  current
                  currentState
                  isSuspended
                  ... on SmartFlexVehicleStatus {
                      current
                      isSuspended
                      currentState
                      stateOfChargeLimit {
                        isLimitViolated
                        timestamp
                        upperSocLimit
                      }
                  }
              }
              alerts {
                  message
                  publishedAt
              }
              ... on SmartFlexVehicle {
                  id
                  name
                  chargePointVariant {
                    amperage
                    integrationStatus
                    isIntegrationLive
                    model
                    powerInKw
                    variantId
                  }
                  alerts {
                    message
                    publishedAt
                  }
                  deviceType
                  make
                  integrationDeviceId
                  model
                  preferences {
                    mode
                    targetType
                    unit
                    schedules {
                      dayOfWeek
                      max
                      min
                      time
                    }
                  }
                  vehicleVariant {
                    year
                    vehicleId
                    model
                    isIntegrationLive
                    integrationStatus
                    batterySize
                  }
                  status {
                    isSuspended
                    currentState
                    current
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


    async def set_device_preferences(self, account_id: str, device_id: str, mode: str, schedules: list, unit: str):
        """Configura las preferencias del dispositivo con la nueva mutación GraphQL."""
        if not self.token:
            if not await self.login():
                return False

        url = "https://api.octopus.energy/v1/graphql"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        mutation = """
        mutation SetDevicePreferences($deviceId: String!, $mode: String!, $schedules: [ScheduleInput!]!, $unit: String!) {
          setDevicePreferences(
            input: {deviceId: $deviceId, mode: $mode, schedules: $schedules, unit: $unit}
          ) {
            id
            ... on SmartFlexVehicle {
              id
              model
              make
              status
            }
          }
        }
        """

        variables = {
            "deviceId": device_id,
            "mode": mode,
            "schedules": schedules,
            "unit": unit
        }

        payload = {
            "query": mutation,
            "variables": variables
        }

        async with self.session.post(url, json=payload, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return "data" in data and data["data"].get("setDevicePreferences") is not None
        return False
    
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

    async def setVehicleChargePreferences(
      self, account_number: str, weekday_soc: int, weekend_soc: int, 
      weekday_time: str, weekend_time: str
):  
      """Envía las preferencias de carga del vehículo a la API de Octopus."""
    
      # Asegúrate de que el token esté disponible
      if not self._token:
          _LOGGER.error("❌ No se ha obtenido un token válido. Llamando a login...")
          login_successful = await self.login()  # Intentar obtener el token
          if not login_successful:
              _LOGGER.error("❌ No se pudo obtener el token. Abortando operación.")
              return {"success": False, "errors": ["No se pudo obtener el token de autenticación."]}

      mutation = """
      mutation vehicleChargingPreferences($input: VehicleChargingPreferencesInput!) {
        setVehicleChargePreferences(input: $input) {
          __typename
        }
      }
      """
      variables = {
          "input": {
              "accountNumber": account_number,
              "weekdayTargetSoc": weekday_soc,
              "weekendTargetSoc": weekend_soc,
              "weekdayTargetTime": weekday_time,
              "weekendTargetTime": weekend_time,
          }
      }

      headers = {
          "authorization": self._token,  # Asegúrate de que `self._token` esté correctamente definido
          "Content-Type": "application/json"
      }

      # Usamos el mismo esquema que en `login` con `GraphqlClient`
      client = GraphqlClient(endpoint=GRAPH_QL_ENDPOINT, headers=headers)

      try:
          response = await client.execute_async(mutation, variables)

          if "errors" in response:
              _LOGGER.error(f"❌ Error al establecer preferencias de carga: {response['errors']}")
              return {"success": False, "errors": response["errors"]}

          _LOGGER.info("✅ Preferencias de carga del vehículo actualizadas correctamente.")
          return response.get("data", {}).get("setVehicleChargePreferences", {})

      except aiohttp.ClientError as e:
          _LOGGER.error(f"⚠️ Error de red en setVehicleChargePreferences: {e}")
          return {"success": False, "errors": [str(e)]}

