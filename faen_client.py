#!/usr/bin/env python3
"""
FAEN API Client for authentication and data retrieval
"""

import requests
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urljoin

from console_utils import print_section, print_info, print_success, print_error, print_data, print_warning


class FaenApiClient:
    """Client for interacting with the FAEN API"""
    
    def __init__(self, base_url: str, username: str, password: str):
        """
        Initialize the FAEN API client
        
        Args:
            base_url: Base URL of the FAEN API
            username: Username for authentication
            password: Password for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.access_token: Optional[str] = None
        self.token_type: str = "Bearer"
        self.session = requests.Session()
    
    def authenticate(self) -> bool:
        """
        Authenticate with the FAEN API using OAuth2 password flow
        
        Returns:
            True if authentication successful, False otherwise
        """
        print_section("🔐 Authentication")
        print_info(f"Authenticating as: {self.username}")
        
        token_url = urljoin(self.base_url + '/', 'token')
        print_data("Token URL", token_url, 1)
        
        # Prepare form data for OAuth2 password flow
        auth_data = {
            'username': self.username,
            'password': self.password,
            'grant_type': 'password'
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        try:
            print_info("Sending authentication request...")
            response = self.session.post(
                token_url,
                data=auth_data,
                headers=headers
            )
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data['access_token']
            self.token_type = token_data.get('token_type', 'Bearer')
            
            # Set authorization header for future requests
            self.session.headers.update({
                'Authorization': f'{self.token_type} {self.access_token}'
            })
            
            print_success(f"✓ Authentication successful!")
            print_data("Token type", self.token_type, 1)
            print_data("Token preview", f"{self.access_token[:20]}...{self.access_token[-10:]}", 1)
            return True
            
        except requests.exceptions.RequestException as e:
            print_error(f"Authentication failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print_data("Response status", str(e.response.status_code), 1)
                print_data("Response content", e.response.text[:200], 1)
            return False
    
    def query_consumption(self, 
                         query: Dict[str, Any], 
                         limit: int = 100, 
                         sort: Optional[str] = None,
                         eumed: bool = False) -> List[Dict[str, Any]]:
        """
        Query consumption data using POST request
        
        Args:
            query: MongoDB query document
            limit: Maximum number of results to return
            sort: Sort key (e.g., "+datetime")
            eumed: Whether to return EUMED-compliant JSON-LD format
            
        Returns:
            List of consumption data records
        """
        if not self.access_token:
            if not self.authenticate():
                raise Exception("Authentication required before making API calls")
        
        print_section("📊 Querying Consumption Data")
        consumption_url = urljoin(self.base_url + '/', 'consumption/query')
        print_data("Endpoint", consumption_url, 1)
        
        request_body = {
            'query': query,
            'limit': limit,
            'eumed': eumed
        }
        
        if sort:
            request_body['sort'] = sort
            print_data("Sort order", sort, 1)
        
        print_data("Limit", str(limit), 1)
        print_data("EUMED format", str(eumed), 1)
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        try:
            print_info("Sending query request...")
            response = self.session.post(
                consumption_url,
                json=request_body,
                headers=headers
            )
            response.raise_for_status()
            
            data = response.json()
            record_count = len(data) if isinstance(data, list) else 1
            print_success(f"✓ Retrieved {record_count} consumption records")
            return data
            
        except requests.exceptions.RequestException as e:
            print_error(f"Failed to query consumption data: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print_data("Response status", str(e.response.status_code), 1)
                print_data("Response content", e.response.text[:200], 1)
            raise
    
    def query_generation(self, 
                        query: Dict[str, Any], 
                        limit: int = 100, 
                        sort: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Query generation data using GET request with URL parameters
        
        Args:
            query: MongoDB query document
            limit: Maximum number of results to return
            sort: Sort key (e.g., "+datetime")
            
        Returns:
            List of generation data records
        """
        if not self.access_token:
            if not self.authenticate():
                raise Exception("Authentication required before making API calls")
        
        print_section("⚡ Querying Generation Data")
        generation_url = urljoin(self.base_url + '/', 'generation/')
        print_data("Endpoint", generation_url, 1)
        
        # Prepare URL parameters
        import json
        
        params = {
            'query': json.dumps(query),
            'limit': limit
        }
        
        if sort:
            params['sort'] = sort
            print_data("Sort order", sort, 1)
        
        print_data("Limit", str(limit), 1)
        
        try:
            print_info("Sending query request...")
            response = self.session.get(
                generation_url,
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            record_count = len(data) if isinstance(data, list) else 1
            print_success(f"✓ Retrieved {record_count} generation records")
            return data
            
        except requests.exceptions.RequestException as e:
            print_error(f"Failed to query generation data: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print_data("Response status", str(e.response.status_code), 1)
                print_data("Response content", e.response.text[:200], 1)
            raise
    
    def query_weather(self, 
                     query: Dict[str, Any], 
                     limit: int = 100, 
                     sort: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Query weather data using GET request with URL parameters
        
        Args:
            query: MongoDB query document
            limit: Maximum number of results to return
            sort: Sort key (e.g., "+datetime")
            
        Returns:
            List of weather data records
        """
        if not self.access_token:
            if not self.authenticate():
                raise Exception("Authentication required before making API calls")
        
        print_section("🌤️ Querying Weather Data")
        weather_url = urljoin(self.base_url + '/', 'weather/')
        print_data("Endpoint", weather_url, 1)
        
        # Prepare URL parameters
        import json
        from urllib.parse import quote
        
        params = {
            'query': json.dumps(query),
            'limit': limit
        }
        
        if sort:
            params['sort'] = sort
            print_data("Sort order", sort, 1)
        
        print_data("Limit", str(limit), 1)
        
        try:
            print_info("Sending query request...")
            response = self.session.get(
                weather_url,
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            record_count = len(data) if isinstance(data, list) else 1
            print_success(f"✓ Retrieved {record_count} weather records")
            return data
            
        except requests.exceptions.RequestException as e:
            print_error(f"Failed to query weather data: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print_data("Response status", str(e.response.status_code), 1)
                print_data("Response content", e.response.text[:200], 1)
            raise
    
    def get_current_user(self) -> Dict[str, Any]:
        """
        Get current user information
        
        Returns:
            User information dictionary
        """
        if not self.access_token:
            if not self.authenticate():
                raise Exception("Authentication required before making API calls")
        
        print_section("👤 User Information")
        user_url = urljoin(self.base_url + '/', 'users/me/')
        print_data("Endpoint", user_url, 1)
        
        try:
            print_info("Fetching user information...")
            response = self.session.get(user_url)
            response.raise_for_status()
            user_data = response.json()
            
            print_success("✓ User information retrieved")
            print_data("Username", user_data.get('username', 'Unknown'), 1)
            print_data("Email", user_data.get('email', 'Not provided'), 1)
            print_data("Full name", user_data.get('full_name', 'Not provided'), 1)
            print_data("Disabled", str(user_data.get('disabled', False)), 1)
            
            return user_data
            
        except requests.exceptions.RequestException as e:
            print_error(f"Failed to get user info: {e}")
            raise


def create_full_day_query(start_date: Union[date, datetime], end_date: Union[date, datetime]) -> Dict[str, Any]:
    """
    Create a MongoDB query for full days (00:00:00 to 00:00:00 next day)
    
    Args:
        start_date: Start date (date or datetime object) - inclusive
        end_date: End date (date or datetime object) - exclusive
        
    Returns:
        MongoDB query document with full day ranges
    """
    # Convert to date objects if datetime objects are passed
    if isinstance(start_date, datetime):
        start_date = start_date.date()
    if isinstance(end_date, datetime):
        end_date = end_date.date()
    
    # Create datetime objects for start of start_date and start of day after end_date
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date + timedelta(days=1), datetime.min.time())
    
    return {
        "datetime": {
            "$gte": {"$date": start_datetime.isoformat()},
            "$lt": {"$date": end_datetime.isoformat()}  # Use $lt instead of $lte for cleaner boundaries
        }
    }


def create_weather_query(start_date: Union[date, datetime], end_date: Union[date, datetime]) -> Dict[str, Any]:
    """
    Create a MongoDB query for weather data using datetime_utc field
    
    Args:
        start_date: Start date (date or datetime object) - inclusive
        end_date: End date (date or datetime object) - exclusive
        
    Returns:
        MongoDB query document for weather data
    """
    # Convert to date objects if datetime objects are passed
    if isinstance(start_date, datetime):
        start_date = start_date.date()
    if isinstance(end_date, datetime):
        end_date = end_date.date()
    
    # Create datetime objects for start of start_date and start of day after end_date
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date + timedelta(days=1), datetime.min.time())
    
    return {
        "datetime_utc": {
            "$gte": {"$date": start_datetime.isoformat()},
            "$lt": {"$date": end_datetime.isoformat()}
        }
    }


def create_date_range_query(start_date: str, end_date: str) -> Dict[str, Any]:
    """
    Create a MongoDB query for a date range (legacy function - kept for compatibility)
    
    Args:
        start_date: Start date in ISO format (e.g., "2022-07-13T16:00:00+0200")
        end_date: End date in ISO format
        
    Returns:
        MongoDB query document
    """
    return {
        "datetime": {
            "$gte": {"$date": start_date},
            "$lte": {"$date": end_date}
        }
    }