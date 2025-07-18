#!/usr/bin/env python3
"""
Test script for combined dataset creation (generation + weather)
"""

import os
import json
from datetime import date
from dotenv import load_dotenv

from faen_client import FaenApiClient, create_full_day_query, create_weather_query
from data_utils import create_combined_dataset_and_datapoints, save_dataset_definition
from console_utils import print_section, print_info, print_success, print_error, print_data

def test_combined_dataset():
    """Test the combined dataset creation with generation and weather data"""
    
    # Load environment variables
    load_dotenv()
    
    # Get configuration
    faen_api_url = os.getenv("FAEN_API_URL")
    faen_username = os.getenv("FAEN_USERNAME") 
    faen_password = os.getenv("FAEN_PASSWORD")
    
    if not all([faen_api_url, faen_username, faen_password]):
        print_error("Missing required environment variables:")
        print_error("FAEN_API_URL, FAEN_USERNAME, FAEN_PASSWORD")
        return False
    
    print_section("🧪 Testing Combined Dataset Creation")
    print_info(f"API URL: {faen_api_url}")
    print_info(f"Username: {faen_username}")
    
    # Initialize client
    client = FaenApiClient(faen_api_url, faen_username, faen_password)
    
    # Test date range (small range for testing)
    start_date = date(2025, 5, 1)
    end_date = date(2025, 5, 2)  # Just 2 days for testing
    
    print_info(f"Date range: {start_date} to {end_date}")
    
    try:
        print_section("🔐 Authentication")
        if not client.authenticate():
            print_error("Authentication failed!")
            return False
        
        print_section("⚡ Fetching Generation Data")
        generation_query = create_full_day_query(start_date, end_date)
        print_data("Query", str(generation_query), 1)
        
        generation_data = client.query_generation(
            query=generation_query,
            limit=200,
            sort="+datetime"
        )
        
        print_success(f"✓ Retrieved {len(generation_data)} generation records")
        if generation_data:
            sample = generation_data[0]
            print_data("Sample user_id", sample.get('user_id', 'N/A'), 1)
            print_data("Sample generation_kwh", sample.get('data', {}).get('generation_kwh', 'N/A'), 1)
        
        print_section("🌤️ Fetching Weather Data")
        weather_query = create_weather_query(start_date, end_date)
        print_data("Query", str(weather_query), 1)
        
        weather_data = client.query_weather(
            query=weather_query,
            limit=200,
            sort="+datetime_utc"
        )
        
        print_success(f"✓ Retrieved {len(weather_data)} weather records")
        if weather_data:
            sample = weather_data[0]
            print_data("Sample temperature (ta)", sample.get('ta', 'N/A'), 1)
            print_data("Sample humidity (hr)", sample.get('hr', 'N/A'), 1)
        
        print_section("🔧 Creating Combined Dataset")
        
        # Create combined dataset and datapoints
        dataset_definition, all_datapoints = create_combined_dataset_and_datapoints(
            start_date, end_date, generation_data, weather_data
        )
        
        print_success(f"✓ Created dataset with {len(all_datapoints)} total datapoints")
        
        # Show dataset summary
        print_info("Dataset Summary:")
        print_data("Dataset name", dataset_definition.get("datacellar:name", "N/A"), 1)
        print_data("Number of timeseries", len(dataset_definition.get("datacellar:timeSeries", [])), 1)
        print_data("Number of dataset fields", len(dataset_definition.get("datacellar:datasetSelfDescription", {}).get("datacellar:datasetFields", [])), 1)
        
        # Show datapoint breakdown
        measurement_counts = {}
        for dp in all_datapoints:
            measurement = dp.get("measurement", "unknown")
            measurement_counts[measurement] = measurement_counts.get(measurement, 0) + 1
        
        print_info("Datapoint breakdown:")
        for measurement, count in measurement_counts.items():
            print_data(f"{measurement} datapoints", str(count), 1)
        
        # Save the dataset definition
        print_section("💾 Saving Dataset Definition")
        saved_path = save_dataset_definition(
            dataset_definition, 
            start_date, 
            end_date, 
            dataset_type="combined"
        )
        
        print_success(f"✓ Dataset definition saved to: {saved_path}")
        
        # Show sample datapoints
        print_section("📊 Sample Datapoints")
        for measurement in measurement_counts.keys():
            sample_dp = next((dp for dp in all_datapoints if dp.get("measurement") == measurement), None)
            if sample_dp:
                print_info(f"Sample {measurement} datapoint:")
                print_data("Value", f"{sample_dp.get('value')} {sample_dp.get('unit')}", 2)
                print_data("Timestamp", sample_dp.get('timestamp'), 2)
                print_data("Timeseries ID", sample_dp.get('timeseries_id'), 2)
        
        print_section("✅ Combined Dataset Test Completed Successfully!")
        print_info(f"Generated dataset covers {len(generation_data)} generation records and {len(weather_data)} weather records")
        print_info(f"Created {len(all_datapoints)} datapoints across {len(measurement_counts)} measurement types")
        
        return True
        
    except Exception as e:
        print_error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_combined_dataset()
    exit(0 if success else 1)