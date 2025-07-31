# FAEN API Client

This directory contains the FAEN API client for retrieving consumption data and processing it for the CDE server.

## Files

- `main.py` - Main client for interacting with the FAEN API
- `env.template` - Environment configuration template
- `data/faen_api_spec.json` - OpenAPI specification for the FAEN API
- `data/faen_consumption_july_2022.json` - Sample consumption data
- `data/faen_consumption_july_2022_definition.json` - Sample dataset definition
- `data/faen_consumption_july_2022.csv` - Sample consumption data in CSV format

## Setup

### Quick Setup (Recommended)

1. Run the setup script:
```bash
./setup.sh
```

2. Create your configuration file from the template:
```bash
vcp env.template .en
```

3. Edit `.env` with your actual credentials if needed:
```bash
# FAEN API Configuration
FAEN_API_URL=https://datacellarvcapi.test.ctic.es
FAEN_USERNAME=datacellar.developer
FAEN_PASSWORD=your_actual_password
CDE_API_URL=https://your-cde-url.com
```

4. Run the script:
```bash
source venv/bin/activate
python main.py
```

### Manual Setup

1. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Quarterly Data Extraction Script

A new script `run_quarterly_data_extraction.sh` has been created to automatically process FAEN data for all quarters from 2022-01-01 to 2024-12-31. This script:

- Processes data in quarterly chunks (12 quarters total)
- Uses non-interactive mode to avoid prompts
- Calls main.py with appropriate date ranges and dataset type
- Automatically handles authentication and data retrieval

### Usage

1. Ensure your `.env` file is properly configured with FAEN and CDE credentials
2. Make the script executable (if not already):
   ```bash
   chmod +x run_quarterly_data_extraction.sh
   ```
3. Run the script:
   ```bash
   ./run_quarterly_data_extraction.sh
   ```

The script will process each quarter sequentially and save dataset definitions and upload data to CDE for each quarter.

3. Configure environment (steps 2-4 above)

### Option 2: Using environment variables

Set environment variables manually:
```bash
export FAEN_API_URL="https://datacellarvcapi.test.ctic.es"
export FAEN_USERNAME="datacellar.developer"
export FAEN_PASSWORD="your_actual_password"
```

## Usage

The script will automatically:
1. Load configuration from `.env` file (if present)
2. Fall back to environment variables
3. Authenticate with the FAEN API
4. Query consumption data for the last 7 days
5. Display the results

```bash
python main.py
```

## Authentication

The client uses OAuth2 password flow as shown in the Swagger UI:
- Content-Type: `application/x-www-form-urlencoded`
- Credentials: username, password, grant_type=password
- Returns: Bearer token for subsequent API calls

## API Endpoints

### Authentication
- `POST /token` - Get access token

### Data Retrieval
- `POST /consumption/query` - Query consumption data with MongoDB-style queries
- `GET /users/me/` - Get current user information

## Example Query

```python
query = {
    "datetime": {
        "$gte": {"$date": "2022-07-13T16:00:00+0200"},
        "$lte": {"$date": "2022-07-15T16:00:00+0200"}
    }
}
```
