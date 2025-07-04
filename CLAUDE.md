# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the FAEN API client directory within the CDE (Data Cellar) server project. FAEN is a Spanish energy consumption data provider, and this client retrieves consumption data and integrates it with the CDE internal API for storage and processing.

## Core Architecture

### Main Components

- **FAEN API Client (`FaenApiClient`)**: Handles OAuth2 authentication and data retrieval from the FAEN API
  - Supports consumption, generation, and weather data endpoints
  - OAuth2 password flow authentication
  - MongoDB-style query support
- **CDE API Client (`CDEApiClient`)**: Manages dataset uploads and datapoint submissions to the CDE internal API
- **Dataset Generation**: Transforms FAEN data into CDE-compatible JSON-LD dataset definitions
  - Support for consumption-only datasets (legacy)
  - Support for combined generation + weather datasets (new)
- **Data Transformation**: Converts FAEN records to CDE datapoint format for timeseries storage
  - Generation data: `generation_kwh` → `generatedEnergy` timeseries
  - Weather data: `ta` → `temperature`, `hr` → `humidityLevel` timeseries

### API Integration Flow

1. **Authentication**: OAuth2 password flow with FAEN API using form-encoded credentials
2. **Data Retrieval**: MongoDB-style queries to fetch consumption data from FAEN
3. **Dataset Creation**: Generate JSON-LD dataset definitions from retrieved data
4. **CDE Upload**: POST dataset definitions and individual datapoints to CDE API
5. **Timeseries Mapping**: Map FAEN user IDs to CDE timeseries IDs for datapoint association

## Common Commands

### Running the Client
```bash
# Run from FAEN directory (recommended)
cd data/FAEN
python faen_consumption_client.py

# Run from project root
python data/FAEN/faen_consumption_client.py
```

### Configuration Setup
```bash
# Create local configuration
cp config_example.env .env
# Edit .env with actual credentials
```

### Testing Environment Loading
```bash
cd data/FAEN
python test_dotenv_behavior.py
```

## Environment Configuration

### Configuration Priority Order
1. **Local `.env` file** (data/FAEN/.env) - Highest priority
2. **Environment variables** 
3. **Parent directory .env files** (searched upward)

### Required Environment Variables
- `FAEN_API_URL`: Base URL for FAEN API (e.g., https://datacellarvcapi.test.ctic.es)
- `FAEN_USERNAME`: Username for FAEN API authentication 
- `FAEN_PASSWORD`: Password for FAEN API authentication
- `CDE_API_URL`: Base URL for CDE internal API (default: http://localhost:5000)

### Configuration Notes
- Script automatically removes `/docs` suffix from FAEN_API_URL if present
- Local .env file takes precedence over all other configuration sources
- Script works when run from any directory but loads its own .env file first

## Data Flow Architecture

### FAEN Data Structure
- **Consumption Records**: User ID, datetime, energy consumption (kWh)
- **Generation Records**: User ID, datetime, energy generation (kWh), type, nominal power
- **Weather Records**: Station-based, datetime_utc, temperature (ta), humidity (hr), and other meteorological parameters
- **MongoDB Queries**: Date range filtering using MongoDB Extended JSON format
- **Authentication**: Bearer token required for all data endpoints

### CDE Integration
- **Dataset Definitions**: JSON-LD format with datacellar namespace
  - Consumption datasets: Single measurement type (`consumedEnergy`)
  - Combined datasets: Multiple measurement types (`generatedEnergy`, `temperature`, `humidityLevel`)
- **Timeseries**: Individual timeseries per user/measurement with metadata
- **Datapoints**: Individual measurements with timestamps and values embedded in timeseries
- **Health Checks**: CDE API health endpoint for connectivity verification

## Development Notes

### API Endpoints Used
- **FAEN**: 
  - `/token` - OAuth2 authentication
  - `POST /consumption/query` - Consumption data (JSON body)
  - `GET /generation/` - Generation data (URL parameters)
  - `GET /weather/` - Weather data (URL parameters)
  - `/users/me/` - User information
- **CDE**: `/api/health`, `/api/dataset`, `/api/timeseries`

### Error Handling
- Comprehensive error reporting with colored console output
- User confirmation prompts at critical steps with proper exit handling
- Script exits cleanly if CDE API is unreachable or FAEN authentication fails
- Graceful handling of Ctrl+C interruption at any point
- Batch processing with individual failure tracking
- All "No" responses to confirmation prompts result in clean exit


