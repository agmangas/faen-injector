### Example datasetFields entry for Generation

```json
"datacellar:datasetFields": [
  {
    "@type": "datacellar:DatasetField",
    "datacellar:datasetFieldID": 1,
    "datacellar:name": "generatedEnergy",
    "datacellar:description": "The generated energy of a PV in kWh",
    "datacellar:timeseriesMetadataType": "datacellar:PVPanel",
    "datacellar:fieldType": {
      "@type": "datacellar:FieldType",
      "datacellar:unit": "kWh",
      "datacellar:averagable": false,
      "datacellar:summable": true,
      "datacellar:anonymizable": false
    }
  }
]
```

### Example datasetFields entry for Temperature

```json
"datacellar:datasetFields": [
  {
    "@type": "datacellar:DatasetField",
    "datacellar:datasetFieldID": 2,
    "datacellar:name": "temperature",
    "datacellar:description": "Ambient temperature in Celsius",
    "datacellar:timeseriesMetadataType": "datacellar:PVPanel",
    "datacellar:fieldType": {
      "@type": "datacellar:FieldType",
      "datacellar:unit": "C",
      "datacellar:averagable": true,
      "datacellar:summable": false,
      "datacellar:anonymizable": false
    }
  }
]
```

### Example datasetFields entry for Humidity

```json
"datacellar:datasetFields": [
  {
    "@type": "datacellar:DatasetField",
    "datacellar:datasetFieldID": 3,
    "datacellar:name": "humidityLevel",
    "datacellar:description": "Humidity level in percentage",
    "datacellar:timeseriesMetadataType": "datacellar:PVPanel",
    "datacellar:fieldType": {
      "@type": "datacellar:FieldType",
      "datacellar:unit": "Percent",
      "datacellar:averagable": true,
      "datacellar:summable": false,
      "datacellar:anonymizable": false
    }
  }
]
```

### Example timeSeriesMetaData entry for Generation

```json
"datacellar:timeSeriesMetadata": {
  "@type": "datacellar:PVPanel",
  "datacellar:deviceID": "user-8647f405-0e74-4dfd-8e54-9be990fb982e",
}
```

### Example timeSeriesMetaData entry for Temperature

PARAMETER OMITTED

### Example timeSeriesMetaData entry for Humidity

PARAMETER OMITTED
