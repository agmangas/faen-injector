#!/usr/bin/env python3
"""
Data transformation utilities for dataset generation and format conversion
"""

import json
from datetime import datetime, date
from typing import Dict, List, Any, Union
from pathlib import Path

from console_utils import print_info, print_success, print_error, print_data, print_warning


def save_dataset_definition(dataset_definition: Dict[str, Any], start_date: Union[date, datetime], end_date: Union[date, datetime]) -> str:
    """
    Save the dataset definition to a JSON file
    
    Args:
        dataset_definition: The dataset definition dictionary
        start_date: Start date (used for filename)
        end_date: End date (used for filename)
        
    Returns:
        Path to the saved file
    """
    # Convert to date objects if datetime objects are passed
    if isinstance(start_date, datetime):
        start_date = start_date.date()
    if isinstance(end_date, datetime):
        end_date = end_date.date()
    
    # Create filename with date range
    filename = f"faen_dataset_definition_{start_date}_to_{end_date}.json"
    
    # Save to the same directory as the script or create a datasets subdirectory
    script_dir = Path(__file__).parent
    datasets_dir = script_dir / "datasets"
    datasets_dir.mkdir(exist_ok=True)
    
    file_path = datasets_dir / filename
    
    try:
        print_info(f"Saving dataset definition to: {file_path}")
        
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(dataset_definition, file, indent=2, ensure_ascii=False)
        
        print_success(f"✓ Dataset definition saved successfully")
        print_data("File path", str(file_path), 1)
        print_data("File size", f"{file_path.stat().st_size:,} bytes", 1)
        
        return str(file_path)
        
    except Exception as e:
        print_error(f"✗ Failed to save dataset definition: {e}")
        raise


def transform_faen_to_datapoints(faen_data: List[Dict[str, Any]], timeseries_mapping: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Transform FAEN consumption data into CDE datapoint format
    
    Args:
        faen_data: List of FAEN consumption records
        timeseries_mapping: Dictionary mapping user_id to timeseries_id
        
    Returns:
        List of datapoint dictionaries ready for CDE API
    """
    datapoints = []
    skipped_records = 0
    missing_timeseries = 0
    
    print_info(f"Transforming {len(faen_data)} FAEN records to CDE datapoints")
    
    for i, record in enumerate(faen_data):
        user_id = record.get('user_id')
        # Extract consumption from nested data object
        data_obj = record.get('data', {})
        consumption_value = data_obj.get('energy_consumption_kwh')
        datetime_str = record.get('datetime')
        
        # Skip records with missing essential data
        if not user_id or consumption_value is None or not datetime_str:
            skipped_records += 1
            continue
        
        # Get the corresponding timeseries ID
        timeseries_id = timeseries_mapping.get(str(user_id))
        if not timeseries_id:
            missing_timeseries += 1
            continue
        
        # Ensure timestamp is in ISO format with Z suffix
        timestamp = datetime_str
        if not timestamp.endswith('Z') and not timestamp.endswith('+00:00'):
            # Parse datetime and convert to UTC ISO format
            try:
                if 'T' in timestamp:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                else:
                    # Handle date-only format
                    dt = datetime.fromisoformat(timestamp)
                timestamp = dt.isoformat() + 'Z'
            except ValueError:
                print_warning(f"⚠ Invalid datetime format: {timestamp}")
                continue
        
        datapoint = {
            "measurement": "consumedEnergy",
            "unit": "kWh",
            "value": float(consumption_value),
            "timestamp": timestamp,
            "timeseries_id": timeseries_id
        }
        
        datapoints.append(datapoint)
    
    # Print summary
    print_success(f"✓ Transformed {len(datapoints)} FAEN records to datapoints")
    if skipped_records > 0:
        print_warning(f"⚠ Skipped {skipped_records} records with missing data (user_id, consumption, or datetime)")
    if missing_timeseries > 0:
        print_warning(f"⚠ Skipped {missing_timeseries} records with no matching timeseries")
    
    return datapoints


def generate_dataset_definition(start_date: Union[date, datetime], end_date: Union[date, datetime], faen_data: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Generate a dataset definition JSON-LD document based on the date range and FAEN data
    
    Args:
        start_date: Start date (date or datetime object)
        end_date: End date (date or datetime object)
        faen_data: List of FAEN consumption records to extract user_ids from
        
    Returns:
        Dataset definition dictionary in JSON-LD format
    """
    # Convert to date objects if datetime objects are passed
    if isinstance(start_date, datetime):
        start_date = start_date.date()
    if isinstance(end_date, datetime):
        end_date = end_date.date()
    
    # Generate title based on date range (assuming full months)
    start_month_name = start_date.strftime("%B")
    end_month_name = end_date.strftime("%B")
    start_year = start_date.year
    end_year = end_date.year
    
    if start_date.year == end_date.year:
        if start_date.month == end_date.month:
            # Same month and year
            title = f"FAEN Consumption {start_month_name} {start_year}"
        else:
            # Different months, same year
            title = f"FAEN Consumption {start_month_name}-{end_month_name} {start_year}"
    else:
        # Different years
        title = f"FAEN Consumption {start_month_name} {start_year} - {end_month_name} {end_year}"
    
    # Create ISO datetime strings for the time series (start of start_date to end of end_date)
    timeseries_start = datetime.combine(start_date, datetime.min.time()).isoformat() + "Z"
    # Adjust end to be 23:59:59 of the end_date
    timeseries_end = datetime.combine(end_date, datetime.max.time()).replace(microsecond=0).isoformat() + "Z"
    
    # Extract unique user_ids from FAEN data
    unique_user_ids = []
    if faen_data:
        user_ids_set = set()
        for record in faen_data:
            user_id = record.get('user_id')
            if user_id and user_id not in user_ids_set:
                user_ids_set.add(user_id)
                unique_user_ids.append(user_id)
        unique_user_ids.sort()  # Sort for consistent ordering
    
    # If no FAEN data provided, create a single generic timeseries
    if not unique_user_ids:
        unique_user_ids = ["generic_user"]
    
    print_info(f"Creating timeseries for {len(unique_user_ids)} users: {', '.join(map(str, unique_user_ids))}")
    
    # Create timeseries entries for each user
    timeseries_entries = []
    for idx, user_id in enumerate(unique_user_ids, 1):
        timeseries_entry = {
            "@type": "datacellar:TimeSeries",
            "datacellar:datasetFieldID": 1,
            "datacellar:startDate": timeseries_start,
            "datacellar:endDate": timeseries_end,
            "datacellar:timeZone": "0",
            "datacellar:granularity": "Hourly",
            "datacellar:dataPoints": [],
            "datacellar:timeSeriesMetadata": {
                "@type": "datacellar:EnergyMeter",
                "datacellar:deviceID": user_id,
                "datacellar:loadType": "aggregate"
            }
        }
        timeseries_entries.append(timeseries_entry)
    
    # Dataset definition template based on faen_consumption_july_2022_definition.json
    dataset_definition = {
        "@context": {
            "id": "@id",
            "type": "@type",
            "graph": "@graph",
            "datacellar": "http://datacellar.org/schema#",
            "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
            "sh": "http://www.w3.org/ns/shacl#",
            "xsd": "http://www.w3.org/2001/XMLSchema#",
            "datacellar:capacity": {"@type": "xsd:float"},
            "datacellar:elevation": {"@type": "xsd:float"},
            "datacellar:floorArea": {"@type": "xsd:float"},
            "datacellar:insulationSurface": {"@type": "xsd:float"},
            "datacellar:latitude": {"@type": "xsd:float"},
            "datacellar:longitude": {"@type": "xsd:float"},
            "datacellar:openingsArea": {"@type": "xsd:float"},
            "datacellar:orientation": {"@type": "xsd:float"},
            "datacellar:startDate": {"@type": "xsd:dateTime"},
            "datacellar:endDate": {"@type": "xsd:dateTime"},
            "datacellar:tilt": {"@type": "xsd:float"},
            "datacellar:timestamp": {"@type": "xsd:dateTime"},
            "datacellar:totalAnnualEnergyConsumption": {"@type": "xsd:float"},
            "datacellar:value": {"@type": "xsd:float"}
        },
        "@type": "datacellar:Dataset",
        "datacellar:name": title,
        "datacellar:description": f"Dataset covering the consumption of FAEN users from {start_date.isoformat()} to {end_date.isoformat()}",
        "datacellar:datasetDescription": {
            "@type": "datacellar:DatasetDescription",
            "datacellar:datasetDescriptionID": 1,
            "datacellar:datasetMetadataTypes": [
                "datacellar:GeoLocalizedDataset",
                "datacellar:Installation"
            ],
            "datacellar:datasetFields": [{
                "@type": "datacellar:DatasetField",
                "datacellar:datasetFieldID": 1,
                "datacellar:name": "consumedEnergy",
                "datacellar:description": "The consumption of a household in kWh",
                "datacellar:timeseriesMetadataType": "datacellar:EnergyMeter",
                "datacellar:fieldType": {
                    "@type": "datacellar:FieldType",
                    "datacellar:unit": "kWh",
                    "datacellar:averagable": True,
                    "datacellar:summable": False,
                    "datacellar:anonymizable": False
                }
            }]
        },
        "datacellar:timeSeries": timeseries_entries,
        "datacellar:datasetMetadata": [{
            "@type": "datacellar:Installation",
            "datacellar:installationType": "localEnergyCommunity",
            "datacellar:capacity": 100.0,
            "datacellar:capacityUnit": "kW"
        }]
    }
    
    return dataset_definition