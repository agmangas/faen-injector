#!/usr/bin/env python3
"""
CDE API Client for health checks, dataset upload, and datapoint management
"""

import requests
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin
from pathlib import Path

from console_utils import print_info, print_success, print_error, print_data, print_warning


class CDEApiClient:
    """Client for interacting with the CDE Internal API"""
    
    def __init__(self, base_url: str):
        """
        Initialize the CDE API client
        
        Args:
            base_url: Base URL of the CDE Internal API
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        # Note: Don't set Content-Type globally as it interferes with multipart/form-data
    
    def check_health(self) -> Dict[str, Any]:
        """
        Check if the CDE Internal API is healthy and accessible
        
        Returns:
            Health status dictionary or None if unreachable
        """
        health_url = urljoin(self.base_url + '/', 'api/health')
        
        try:
            print_info("Checking CDE API health...")
            response = self.session.get(
                health_url, 
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            
            health_data = response.json()
            
            if response.status_code == 200:
                print_success("✓ CDE API is healthy")
            elif response.status_code == 503:
                print_warning("⚠ CDE API is running but some services are unhealthy")
            else:
                print_error(f"✗ CDE API health check returned status {response.status_code}")
            
            return health_data
            
        except requests.exceptions.RequestException as e:
            print_error(f"✗ CDE API is unreachable: {e}")
            return None
    
    def upload_dataset(self, dataset_file_path: str) -> Dict[str, Any]:
        """
        Upload a dataset definition file to the CDE
        
        Args:
            dataset_file_path: Path to the dataset definition JSON file
            
        Returns:
            Response data from CDE API or None if failed
        """
        upload_url = urljoin(self.base_url + '/', 'api/dataset')
        
        try:
            print_info(f"Uploading dataset: {dataset_file_path}")
            print_data("Upload URL", upload_url, 1)
            
            # Open file and prepare form data
            with open(dataset_file_path, 'rb') as file:
                files = {
                    'file': (
                        Path(dataset_file_path).name,  # filename
                        file,  # file object
                        'application/json'  # mime type
                    )
                }
                
                response = self.session.post(
                    upload_url,
                    files=files,
                    timeout=30  # Increase timeout for file upload
                )
            
            if response.status_code in [200, 201]:  # Accept both 200 OK and 201 Created
                print_success("✓ Dataset uploaded successfully to CDE")
                try:
                    upload_data = response.json()
                    return upload_data
                except:
                    # If response is not JSON, return a success indicator
                    return {"status": "success", "message": "Dataset uploaded successfully"}
            else:
                print_error(f"✗ Dataset upload failed with status {response.status_code}")
                print_data("Response content", response.text[:500], 1)
                return None
                
        except requests.exceptions.RequestException as e:
            print_error(f"✗ Dataset upload failed: {e}")
            return None
        except FileNotFoundError:
            print_error(f"✗ Dataset file not found: {dataset_file_path}")
            return None
    
    def get_timeseries(self, dataset_id: str = None, dataset_name: str = None) -> List[Dict[str, Any]]:
        """
        Get timeseries from CDE, optionally filtered by dataset ID or name
        
        Args:
            dataset_id: Optional dataset ID to filter timeseries (preferred)
            dataset_name: Optional dataset name to filter timeseries (fallback)
            
        Returns:
            List of timeseries data or None if failed
        """
        timeseries_url = urljoin(self.base_url + '/', 'api/timeseries')
        
        try:
            print_info("Fetching timeseries from CDE...")
            
            params = {}
            if dataset_id:
                params['dataset_id'] = dataset_id
                print_data("Dataset ID filter", dataset_id, 1)
            elif dataset_name:
                params['dataset'] = dataset_name
                print_data("Dataset name filter", dataset_name, 1)
            
            response = self.session.get(
                timeseries_url,
                params=params,
                timeout=30,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                timeseries_data = response.json()
                print_success(f"✓ Retrieved {len(timeseries_data)} timeseries")
                return timeseries_data
            else:
                print_error(f"✗ Failed to get timeseries with status {response.status_code}")
                print_data("Response content", response.text[:500], 1)
                return None
                
        except requests.exceptions.RequestException as e:
            print_error(f"✗ Failed to get timeseries: {e}")
            return None
    
    def add_datapoint(self, measurement: str, unit: str, value: float, timestamp: str, timeseries_id: str) -> bool:
        """
        Add a single datapoint to a timeseries
        
        Args:
            measurement: Name of the measurement (e.g., "consumedEnergy")
            unit: Unit of measurement (e.g., "kWh")
            value: The data value
            timestamp: ISO timestamp string
            timeseries_id: UUID of the timeseries
            
        Returns:
            True if successful, False otherwise
        """
        datapoint_url = urljoin(self.base_url + '/', 'api/timeseries')
        
        datapoint = {
            "measurement": measurement,
            "unit": unit,
            "value": value,
            "timestamp": timestamp,
            "timeseries": timeseries_id
        }
        
        try:
            response = self.session.post(
                datapoint_url,
                json=datapoint,
                timeout=30,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code in [200, 201]:
                return True
            else:
                print_error(f"✗ Failed to add datapoint with status {response.status_code}")
                print_data("Response content", response.text[:200], 1)
                return False
                
        except requests.exceptions.RequestException as e:
            print_error(f"✗ Failed to add datapoint: {e}")
            return False
    
    def add_datapoints_batch(self, datapoints: List[Dict[str, Any]], batch_size: int = 100) -> Dict[str, int]:
        """
        Add multiple datapoints in batches
        
        Args:
            datapoints: List of datapoint dictionaries
            batch_size: Number of datapoints to send per batch
            
        Returns:
            Dictionary with success/failure counts
        """
        print_info(f"Adding {len(datapoints)} datapoints in batches of {batch_size}")
        
        total_success = 0
        total_failed = 0
        
        # Process datapoints in batches
        for i in range(0, len(datapoints), batch_size):
            batch = datapoints[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(datapoints) + batch_size - 1) // batch_size
            
            print_info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} datapoints)")
            
            batch_success = 0
            for datapoint in batch:
                if self.add_datapoint(**datapoint):
                    batch_success += 1
                else:
                    total_failed += 1
            
            total_success += batch_success
            print_data("Batch success", f"{batch_success}/{len(batch)}", 1)
        
        print_success(f"✓ Successfully added {total_success} datapoints")
        if total_failed > 0:
            print_error(f"✗ Failed to add {total_failed} datapoints")
        
        return {
            "success": total_success,
            "failed": total_failed,
            "total": len(datapoints)
        }