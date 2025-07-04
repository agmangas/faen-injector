#!/usr/bin/env python3
"""
Test script for new FAEN API calls (generation and weather)
"""

import os
from datetime import date
from dotenv import load_dotenv

from faen_client import FaenApiClient, create_full_day_query, create_weather_query
from console_utils import print_section, print_info, print_success, print_error

def test_api_calls():
    """Test the new generation and weather API calls"""
    
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
    
    print_section("🧪 Testing New API Calls")
    print_info(f"API URL: {faen_api_url}")
    print_info(f"Username: {faen_username}")
    
    # Initialize client
    client = FaenApiClient(faen_api_url, faen_username, faen_password)
    
    # Test date range (small range for testing)
    start_date = date(2025, 5, 1)
    end_date = date(2025, 5, 2)  # Just 2 days for testing
    
    try:
        print_section("🔐 Authentication Test")
        if not client.authenticate():
            print_error("Authentication failed!")
            return False
        
        print_section("⚡ Testing Generation API")
        generation_query = create_full_day_query(start_date, end_date)
        print_info(f"Query: {generation_query}")
        
        generation_data = client.query_generation(
            query=generation_query,
            limit=50,
            sort="+datetime"
        )
        
        print_success(f"✓ Generation API working! Got {len(generation_data)} records")
        if generation_data:
            sample = generation_data[0]
            print_info(f"Sample record keys: {list(sample.keys())}")
            if 'data' in sample:
                print_info(f"Sample data keys: {list(sample['data'].keys())}")
        
        print_section("🌤️ Testing Weather API")
        weather_query = create_weather_query(start_date, end_date)
        print_info(f"Query: {weather_query}")
        
        weather_data = client.query_weather(
            query=weather_query,
            limit=50,
            sort="+datetime_utc"
        )
        
        print_success(f"✓ Weather API working! Got {len(weather_data)} records")
        if weather_data:
            sample = weather_data[0]
            print_info(f"Sample record keys: {list(sample.keys())}")
            # Check for ta and hr fields
            ta = sample.get('ta')
            hr = sample.get('hr')
            print_info(f"Temperature (ta): {ta}")
            print_info(f"Humidity (hr): {hr}")
        
        print_section("✅ All Tests Passed!")
        return True
        
    except Exception as e:
        print_error(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_api_calls()
    exit(0 if success else 1)