### Consumption
_/consumption_

```json
{
    "_id": "6500794dac9fdc83ecba292b",
    "user_id": "user-438a87c4-ac07-4d97-9d82-b4b3ef3973f7",
    "local_date_str": "2022-07-13",
    "datetime": "2022-07-13T14:00:00",
    "data": {
      "energy_consumption_kwh": 0.16
    }
  },
```

_/consumption/average/month_

```json
{
    "avg_energy_consumption_kwh": 1.07,
    "user_id": "user-438a87c4-ac07-4d97-9d82-b4b3ef3973f7",
    "date_utc": "2021-06-01T00:00:00"
  }
```

### Historical Generation
_/generation_

```json
{
    "_id": "6500634d2838e89d806105ef",
    "user_id": "user-f6726b8b-28c1-4aec-a5b4-8ae41b47180e",
    "local_date_str": "2023-05-23",
    "datetime": "2023-05-22T22:00:00",
    "data": {
      "type": "b11",
      "generation_kwh": 0,
      "nominal_power_w": 20000
    }
  }
```

### Historical Weather
_/weather_

```json
{
    "_id": "65026171e4e54136b56fbfe1",
    "datetime_utc": "2023-09-13T22:00:00",
    "idema": "1249X",
    "fint": "2023-09-14T00:00:00",
    "ubi": "OVIEDO",
    "alt": 334,
    "dmax": null,
    "dv": null,
    "hr": 92,
    "inso": null,
    "lat": 43.353333,
    "lon": -5.873889,
    "prec": 0,
    "pres": 981.8,
    "pres_nmar": null,
    "stddv": null,
    "stdvv": null,
    "ta": 17.3,
    "tamax": 17.5,
    "tamin": 17.3,
    "tpr": null,
    "ts": 17.1,
    "vmax": null,
    "vv": null,
    "vis": 20,
    "tss5cm": null,
    "pacutp": 0,
    "tss20cm": 20.5
  }
```

### PVGIS
_/pvgiis/hourly-radiation_

```json
{
    "time": "20200101:0010",
    "G(i)": "0.0",
    "H_sun": "0.0",
    "T2m": "2.3",
    "WS10m": "1.52",
    "Int": "0.0"
}
```

### Realtime Consumption
_/realtime-semantic/consumption_

```json
{
    "_id": "67c72e5d7edd437e432b2b0e",
    "meter_id": "https://w3id.org/omega-x/Maia#NameDevice_2",
    "datetime": "2024-11-11T00:03:25",
    "data": {
      "active_power_w": 28310,
      "reactive_power_var": 28490,
      "apparent_power_va": 28490,
      "energy_wh": null
    },
    "measurement_type": "power",
    "reading_type": null,
    "period_seconds": null
  },
```

### Realtime data from Gecko platform
_/realtime_

```json
{
    "_id": "682bc84f722b4a3f6669cc4c",
    "_field": "powerReact",
    "_measurement": "4080f2",
    "_time": "2025-05-20T00:00:00",
    "_value": 31.889421468749998,
    "result": "_result",
    "slaveGroup": "inverter",
    "slaveId": "virtual_inverter_energycom_999999",
    "table": 12,
    "varGroup": "power"
  }
```
