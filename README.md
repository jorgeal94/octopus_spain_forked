# En DESARROLLO
# Componente Octopus Spain Intelligent para Home Assistant

Fork compatible con la integracion original, pero con `domain` distinto para poder instalar ambas a la vez.

## Basado en API KRAKEN

[https://api.oees-kraken.energy/](https://api.oees-kraken.energy/v1/graphql/)


## Instalación

Puedes instalar el componente usando HACS:

??????
### Directa usando _My Home Assistant_
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=MiguelAngelLV&repository=ha-octopus-spain&category=integration)


### Manual
```
HACS -> Integraciones -> Tres puntitos -> Repositorios Personalizados
```
Copias la URL del reposotiro ( https://github.com/MiguelAngelLV/ha-octopus-spain ), como categoría seleccionas _Integración_ y pulsas en _Añadir_.

Dominio de esta integracion: `octopus_spain_intelligent`.


## Configuración

Una vez instalado, ve a _Dispositivos y Servicios -> Añadir Integración_ y busca _Octopus Spain Intelligent_.

El asistente te solicitará tu email y contraseña de [Octopus Energy](https://octopusenergy.es/)
