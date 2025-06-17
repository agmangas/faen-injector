#!/usr/bin/env python3
"""
FAEN API Client for Consumption Data with CDE Integration
Main CLI script that orchestrates the data retrieval and upload workflow
"""

import os
from datetime import date
from dotenv import load_dotenv
from pathlib import Path

# Import our modular components
from console_utils import (
    print_header, print_section, print_success, print_error, print_warning,
    print_info, print_data, print_json_preview, confirm_proceed,
    get_dataset_name_input, get_date_range_input, get_limit_input, Colors
)
from faen_client import FaenApiClient, create_full_day_query
from cde_client import CDEApiClient
from data_utils import (
    generate_dataset_definition, save_dataset_definition,
    transform_faen_to_datapoints
)

# Constants - default values (will be overridden by environment variables)
SAMPLE_RECORDS_DISPLAY = 2  # Number of sample records to show
MAX_USER_IDS_DISPLAY = 5    # Maximum number of user IDs to display
DEFAULT_BATCH_SIZE = 50     # Default batch size for datapoint uploads


def load_configuration():
    """Load configuration from .env files or environment variables"""
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    
    # Option 1: Load .env from script directory (recommended for this use case)
    env_file = script_dir / '.env'
    if env_file.exists():
        load_dotenv(env_file)
        print_success(f"✓ Loaded configuration from: {env_file}")
    else:
        # Option 2: Load .env from current working directory or search upward
        loaded_file = load_dotenv(verbose=False)  # Set to False to reduce noise
        if loaded_file:
            print_success(f"✓ Loaded configuration from: {loaded_file}")
        else:
            print_warning("⚠ No .env file found. Using environment variables or defaults.")


def main():
    """Main function to demonstrate the FAEN API client with CDE integration"""
    
    print_header("FAEN API ➔ CDE Integration Client")
    
    # Load configuration
    load_configuration()
    
    # Load configurable constants from environment variables
    global SAMPLE_RECORDS_DISPLAY, MAX_USER_IDS_DISPLAY, DEFAULT_BATCH_SIZE
    SAMPLE_RECORDS_DISPLAY = int(os.getenv('SAMPLE_RECORDS_DISPLAY', str(SAMPLE_RECORDS_DISPLAY)))
    MAX_USER_IDS_DISPLAY = int(os.getenv('MAX_USER_IDS_DISPLAY', str(MAX_USER_IDS_DISPLAY)))
    DEFAULT_BATCH_SIZE = int(os.getenv('DEFAULT_BATCH_SIZE', str(DEFAULT_BATCH_SIZE)))
    
    # Initial confirmation to start the process
    if not confirm_proceed(
        "This script will connect to FAEN API, retrieve data, and upload to "
        "CDE. Do you want to continue?"
    ):
        print_info("❌ Operation cancelled by user")
        return
    
    print_section("⚙️ Configuration")
    # Configuration - loaded from .env file or environment variables
    faen_base_url = os.getenv('FAEN_API_URL')
    faen_username = os.getenv('FAEN_USERNAME', 'datacellar.developer')
    faen_password = os.getenv('FAEN_PASSWORD')
    
    cde_base_url = os.getenv('CDE_API_URL', 'http://localhost:5000')
    
    # Remove /docs from the FAEN URL if present
    # (it's the Swagger UI URL, not the API base)
    if faen_base_url and faen_base_url.endswith('/docs'):
        faen_base_url = faen_base_url.replace('/docs', '')
        print_warning(
            f"⚠ Adjusted FAEN API URL (removed /docs): {faen_base_url}"
        )
    
    if not faen_base_url:
        print_error("Please set the FAEN_API_URL environment variable")
        return
        
    if not faen_password:
        print_error("Please set the FAEN_PASSWORD environment variable")
        return
    
    print_data("FAEN API URL", faen_base_url, 1)
    print_data("FAEN Username", faen_username, 1)
    print_data("FAEN Password", "*" * len(faen_password), 1)
    print_data("CDE API URL", cde_base_url, 1)
    print_data("Batch Size", str(DEFAULT_BATCH_SIZE), 1)
    print_data("Sample Records Display", str(SAMPLE_RECORDS_DISPLAY), 1)
    print_data("Max User IDs Display", str(MAX_USER_IDS_DISPLAY), 1)
    
    # Create clients
    faen_client = FaenApiClient(faen_base_url, faen_username, faen_password)
    cde_client = CDEApiClient(cde_base_url)
    
    try:
        # Step 1: Check CDE API health
        print_section("🏥 CDE Health Check")
        health_status = cde_client.check_health()
        
        if not health_status:
            print_error("❌ CDE API is not accessible.")
            print_error("❌ Cannot proceed without CDE API connection. Exiting.")
            return
        else:
            print_data("CDE Status", health_status.get('status', 'unknown'), 1)
            print_data("CDE Version", health_status.get('version', 'unknown'), 1)
            print_data("Timestamp", health_status.get('timestamp', 'unknown'), 1)
            
            # Show service status
            services = health_status.get('services', {})
            for service_name, service_info in services.items():
                status = service_info.get('status', 'unknown')
                status_emoji = "✅" if status == "healthy" else "⚠️" if "error" not in status else "❌"
                print_data(f"{service_name.title()} Status", f"{status_emoji} {status}", 2)
        
        # Step 2: Test authentication with FAEN
        if faen_client.authenticate():
            # Get current user info
            user_info = faen_client.get_current_user()
            
            # Confirmation point 1: After successful authentication
            if not confirm_proceed(
                "Authentication successful! Do you want to proceed with data "
                "retrieval configuration?"
            ):
                print_info("❌ Operation cancelled by user")
                return
            
            # Get user input for date range and limit
            start_date, end_date = get_date_range_input()
            limit = get_limit_input()
            
            print_section("📅 Final Configuration Summary")
            today = date.today()
            print_data("Today", str(today), 1)
            print_data("Query start date", f"{start_date} (00:00:00)", 1)
            print_data(
                "Query end date",
                f"{end_date} (inclusive, until 00:00:00 next day)",
                1
            )
            total_days = (end_date - start_date).days + 1
            print_data("Total days", f"{total_days} complete days", 1)
            print_data("Record limit", f"{limit} records maximum", 1)
            
            query = create_full_day_query(start_date, end_date)
            
            print_section("🔍 MongoDB Query")
            print_data("Query type", "Full day range query", 1)
            print_json_preview(query)
            
            # Query consumption data
            consumption_data = faen_client.query_consumption(
                query=query,
                limit=limit,
                sort="+datetime"
            )
            
            print_section("📋 FAEN Results Summary")
            print_data("Total records", str(len(consumption_data)), 1)
            
            # Confirmation point 2: After data retrieval
            if not confirm_proceed(
                f"Retrieved {len(consumption_data)} records from FAEN. Do you "
                f"want to continue with dataset generation?"
            ):
                print_info("❌ Operation cancelled by user")
                return
            
            # Print first few records
            if consumption_data:
                print_section("📊 Sample FAEN Data")
                # Show only limited records to save space
                for i, record in enumerate(consumption_data[:SAMPLE_RECORDS_DISPLAY]):
                    print(
                        f"\n{Colors.BOLD}{Colors.MAGENTA}  Record {i+1}:"
                        f"{Colors.RESET}"
                    )
                    print_json_preview(record)
                
                if len(consumption_data) > SAMPLE_RECORDS_DISPLAY:
                    remaining = len(consumption_data) - SAMPLE_RECORDS_DISPLAY
                    print(
                        f"\n{Colors.GRAY}  ... and {remaining} more records"
                        f"{Colors.RESET}"
                    )
                
                # Generate dataset definition
                print_section("📋 Dataset Definition Generation")
                print_info(
                    "Generating dataset definition from date range..."
                )
                
                dataset_definition = generate_dataset_definition(
                    start_date, end_date, consumption_data
                )
                
                print_success("✓ Dataset definition generated successfully")
                print_data(
                    "Dataset name",
                    dataset_definition.get('datacellar:name', 'Unknown'),
                    1
                )
                print_data(
                    "Dataset description",
                    dataset_definition.get('datacellar:description', 'Unknown'),
                    1
                )
                
                timeseries_list = dataset_definition.get('datacellar:timeSeries', [])
                print_data("Number of timeseries", str(len(timeseries_list)), 1)
                
                if timeseries_list:
                    first_timeseries = timeseries_list[0]
                    print_data(
                        "Time series start",
                        first_timeseries.get('datacellar:startDate', 'Unknown'),
                        1
                    )
                    print_data(
                        "Time series end",
                        first_timeseries.get('datacellar:endDate', 'Unknown'),
                        1
                    )
                    print_data(
                        "Granularity",
                        first_timeseries.get('datacellar:granularity', 'Unknown'),
                        1
                    )
                    
                    # Show user IDs for first few timeseries
                    user_ids = []
                    # Show first few user IDs
                    for ts in timeseries_list[:MAX_USER_IDS_DISPLAY]:
                        metadata = ts.get('datacellar:timeSeriesMetadata', {})
                        user_id = metadata.get('datacellar:deviceID', 'Unknown')
                        user_ids.append(str(user_id))
                    
                    user_ids_display = ', '.join(user_ids)
                    if len(timeseries_list) > MAX_USER_IDS_DISPLAY:
                        additional = len(timeseries_list) - MAX_USER_IDS_DISPLAY
                        user_ids_display += f", ... (+{additional} more)"
                    
                    print_data("User IDs", user_ids_display, 1)
                
                # Get custom dataset name from user
                default_name = dataset_definition.get(
                    'datacellar:name', 'FAEN Dataset'
                )
                custom_name = get_dataset_name_input(default_name)
                
                # Update dataset definition with custom name
                if custom_name != default_name:
                    dataset_definition['datacellar:name'] = custom_name
                    print_info(f"Dataset name updated to: {custom_name}")
                
                # Confirmation point 3: After dataset generation and naming
                if not confirm_proceed(
                    "Dataset definition ready. Do you want to save it to file?"
                ):
                    print_info("❌ Operation cancelled by user")
                    return
                
                # Save dataset definition to filesystem
                print_section("💾 Saving Dataset Definition")
                dataset_file_path = save_dataset_definition(
                    dataset_definition, start_date, end_date
                )
                
                # Confirmation point 4: Before CDE upload
                if not confirm_proceed(
                    "Dataset saved successfully. Do you want to upload it to CDE?"
                ):
                    print_info("❌ CDE upload cancelled by user")
                    print_info(
                        "💡 Dataset file saved locally for manual upload when ready"
                    )
                    return
                
                # Upload dataset to CDE
                print_section("⬆️ Uploading Dataset to CDE")
                upload_successful = False
                dataset_name = dataset_definition.get('datacellar:name', '')
                dataset_id = None
                
                upload_result = cde_client.upload_dataset(dataset_file_path)
                
                if upload_result:
                    upload_successful = True
                    print_success("✓ Dataset successfully uploaded to CDE")
                    
                    # Extract dataset ID from the response
                    dataset_id = upload_result.get('dataset_id')
                    if dataset_id:
                        print_data("Dataset ID", dataset_id, 1)
                    
                    if isinstance(upload_result, dict) and 'message' in upload_result:
                        print_data("CDE Response", upload_result['message'], 1)
                    elif isinstance(upload_result, dict):
                        print_data("CDE Response", str(upload_result), 1)
                    
                    # Confirmation point 5: Before datapoint upload
                    if not confirm_proceed(
                        "Dataset uploaded to CDE successfully. Do you want to "
                        "proceed with uploading datapoints?"
                    ):
                        print_info("❌ Datapoint upload cancelled by user")
                        print_info(
                            "💡 Dataset is available in CDE, datapoints can be "
                            "uploaded separately"
                        )
                        return
                    
                    # Step 3: Get timeseries from CDE and upload datapoints
                    print_section("📊 Uploading Datapoints to CDE")
                    
                    # Fetch timeseries from CDE using dataset ID (preferred)
                    # or name (fallback)
                    timeseries_list = cde_client.get_timeseries(
                        dataset_id=dataset_id, dataset_name=dataset_name
                    )
                    
                    if timeseries_list:
                        # Log all retrieved timeseries IDs
                        print_info("Retrieved timeseries from CDE:")
                        for i, ts in enumerate(timeseries_list, 1):
                            ts_id = ts.get('id', 'Unknown')
                            print_data(f"Timeseries {i}", ts_id, 2)
                        print_data("Total timeseries retrieved", str(len(timeseries_list)), 1)
                        
                        # Create mapping of user_id to timeseries_id
                        timeseries_mapping = {}
                        
                        print_info("Mapping timeseries IDs to user IDs...")
                        for ts in timeseries_list:
                            # Extract user_id from timeseries metadata
                            metadata = ts.get('timeSeriesMetadata', {})
                            device_id = metadata.get('datacellar:deviceID')
                            ts_id = ts.get('id')
                            
                            if device_id and ts_id:
                                timeseries_mapping[str(device_id)] = ts_id
                                print_data(f"User {device_id}", ts_id, 2)
                            else:
                                print_warning(
                                    f"⚠ Missing mapping data - device_id: "
                                    f"{device_id}, ts_id: {ts_id}"
                                )
                        
                        print_data("Total mappings", str(len(timeseries_mapping)), 1)
                        
                        if timeseries_mapping:
                            # Transform FAEN data to CDE datapoint format
                            datapoints = transform_faen_to_datapoints(
                                consumption_data, timeseries_mapping
                            )
                            
                            if datapoints:
                                # Upload datapoints in batches
                                batch_result = cde_client.add_datapoints_batch(
                                    datapoints, batch_size=DEFAULT_BATCH_SIZE
                                )
                                
                                print_section("📈 Datapoint Upload Results")
                                print_data(
                                    "Total datapoints", str(batch_result['total']), 1
                                )
                                print_data(
                                    "Successfully uploaded",
                                    str(batch_result['success']),
                                    1
                                )
                                print_data(
                                    "Failed uploads", str(batch_result['failed']), 1
                                )
                                
                                if batch_result['success'] > 0:
                                    total = batch_result['total']
                                    success = batch_result['success']
                                    success_rate = (success / total) * 100
                                    print_data(
                                        "Success rate", f"{success_rate:.1f}%", 1
                                    )
                                    
                                    if batch_result['failed'] == 0:
                                        print_success(
                                            "🎉 All datapoints uploaded successfully!"
                                        )
                                    else:
                                        failed = batch_result['failed']
                                        print_warning(
                                            f"⚠ {failed} datapoints failed to upload"
                                        )
                            else:
                                print_warning(
                                    "⚠ No valid datapoints generated from FAEN data"
                                )
                        else:
                            print_error("✗ No timeseries mappings found")
                    else:
                        print_error("✗ Failed to retrieve timeseries from CDE")
                        print_warning(
                            "⚠ Cannot upload datapoints without timeseries IDs"
                        )
                else:
                    print_error("✗ Failed to upload dataset to CDE")
                    print_warning(
                        "⚠ Dataset file is saved locally and can be uploaded "
                        "manually"
                    )
                
                print_header("✅ FAEN ➔ CDE Integration Completed")
                print_success(
                    f"✓ Successfully retrieved {len(consumption_data)} FAEN records"
                )
                print_success("✓ Successfully generated dataset definition")
                print_success(
                    f"✓ Dataset definition saved to: {dataset_file_path}"
                )
                
                if upload_successful:
                    print_success("✓ Dataset successfully uploaded to CDE")
                    
                    # Check if datapoints were also uploaded
                    if 'batch_result' in locals():
                        if batch_result['success'] > 0:
                            success_count = batch_result['success']
                            print_success(
                                f"✓ Successfully uploaded {success_count} datapoints "
                                f"to CDE"
                            )
                            if batch_result['failed'] == 0:
                                print_info(
                                    "🎉 Complete integration pipeline executed "
                                    "successfully!"
                                )
                            else:
                                failed_count = batch_result['failed']
                                print_info(
                                    f"⚠ Integration completed with {failed_count} "
                                    f"datapoint upload failures"
                                )
                        else:
                            print_warning(
                                "⚠ Dataset uploaded but no datapoints were "
                                "successfully added"
                            )
                    else:
                        print_warning(
                            "⚠ Dataset uploaded but datapoint upload was not "
                            "attempted"
                        )
                else:
                    print_info(
                        "📁 Dataset ready for manual upload to CDE when available"
                    )
                    
            else:
                print_warning(
                    "⚠ No consumption data found for the specified date range"
                )
                print_info("❌ Cannot proceed without data. Exiting.")
                return
            
        else:
            print_error("❌ FAEN Authentication failed!")
            print_error("❌ Cannot proceed without FAEN API access. Exiting.")
            return
    
    except KeyboardInterrupt:
        print(
            f"\n{Colors.YELLOW}❌ Operation cancelled by user (Ctrl+C)"
            f"{Colors.RESET}"
        )
        return
    except Exception as e:
        print_error(f"❌ Error: {e}")
        return


if __name__ == "__main__":
    main() 