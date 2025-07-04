# FAEN API Client Enhancement Plan

## Overview
Enhance the FAEN API client to create datasets combining generation, temperature, and humidity data from multiple FAEN API endpoints.

## Current State
- Script currently handles only `/consumption` endpoint
- Creates datasets with consumption timeseries only
- Hardcoded for consumption data in `data_utils.py`

## Target State
Create datasets with 3 timeseries:
1. **Generation** (kWh) - from `/generation` endpoint
2. **Temperature** (°C) - from `/weather` endpoint (`ta` parameter)
3. **Humidity** (%) - from `/weather` endpoint (`hr` parameter)

## Data Analysis Results

### Sample Data Analysis
- **Consumption data**: 7 unique users
- **Generation data**: 1 unique user (`user-f6726b8b-28c1-4aec-a5b4-8ae41b47180e`)
- **Weather data**: Station-based (Oviedo, `idema: "1249X"`)
- **No overlapping user_ids** between consumption and generation datasets

### API Endpoints
- **Generation**: `/generation/` - MongoDB-style queries, same as consumption
- **Weather**: `/weather/` - MongoDB-style queries with datetime_utc filter
- **All endpoints return hourly data**

### Weather API Sample
```bash
curl -X 'GET' \
  'https://datacellarvcapi.test.ctic.es/weather/?query=%7B%22datetime_utc%22%3A%20%7B%22%24gte%22%3A%20%7B%22%24date%22%3A%20%222025-05-01T00%3A00%3A00%2B0200%22%7D%2C%20%22%24lte%22%3A%20%7B%22%24date%22%3A%20%222025-06-01T00%3A00%3A00%2B0200%22%7D%7D%7D&limit=10000&sort=%2Bdatetime' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer {token}'
```

## Implementation Tasks

### 1. Add Generation API Call Functionality
- [ ] Add `/generation` endpoint support to API client
- [ ] Use same MongoDB query structure as consumption
- [ ] Handle generation data structure: `generation_kwh`, `type`, `nominal_power_w`

### 2. Add Weather API Call Functionality  
- [ ] Add `/weather` endpoint support to API client
- [ ] Implement URL-encoded MongoDB query for `datetime_utc` field
- [ ] Extract only `ta` (temperature) and `hr` (humidity) parameters
- [ ] Handle null values appropriately

### 3. Enhance data_utils.py
- [ ] Modify `generate_dataset_definition()` to support multiple timeseries types
- [ ] Remove hardcoded consumption-specific logic
- [ ] Support parametric dataset field definitions
- [ ] Update dataset naming and descriptions

### 4. Create Combined Transformation Function
- [ ] New function to transform generation data to CDE datapoints
- [ ] New function to transform weather data to CDE datapoints  
- [ ] Handle timestamp alignment between different data sources
- [ ] Support multiple measurement types in single dataset

### 5. Update Dataset Definition Generator
- [ ] Create datasets with 3 timeseries:
  - Generation: `datacellar:fieldType` with unit "kWh"
  - Temperature: `datacellar:fieldType` with unit "°C" 
  - Humidity: `datacellar:fieldType` with unit "%"
- [ ] Update timeseries metadata types appropriately
- [ ] Modify dataset title generation for combined datasets

### 6. Integrate CLI Interface
- [ ] Add new dataset type option in CLI
- [ ] Update user prompts to support generation+weather datasets
- [ ] Maintain existing consumption-only functionality
- [ ] Use same date range selection for all endpoints

### 7. End-to-End Testing
- [ ] Test API calls for all three endpoints
- [ ] Verify data transformation and alignment
- [ ] Test dataset creation with combined timeseries
- [ ] Validate CDE API integration

## Technical Considerations

### Data Handling
- **Temporal alignment**: All endpoints return hourly data
- **Date ranges**: Same date range for all API calls (user-specified)
- **Missing data**: Keep 0 generation values, handle null weather values
- **Location correlation**: Assume generation and weather locations are correlated

### Dataset Structure
- **One dataset** with **three timeseries**
- Each timeseries contains single measurement type
- No location metadata initially (future enhancement)

### API Query Strategy
- Generation: Same as consumption (user-based)
- Weather: Station-based, no user correlation needed
- All use MongoDB-style date range queries

## Files to Modify
- `data_utils.py` - Core dataset generation logic
- Main script (TBD) - API calls and CLI integration
- Potentially create new utility modules for API abstraction

## Future Enhancements
- [ ] Add location metadata correlation
- [ ] Support multiple weather stations
- [ ] Correlation analysis between generation and weather
- [ ] Additional weather parameters (solar radiation, wind, etc.)

---
*Generated: 2025-07-04*
*Status: Planning phase*