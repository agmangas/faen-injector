#!/usr/bin/env python3
"""
FAEN API Client for Consumption Data with CDE Integration
Main CLI script that orchestrates the data retrieval and upload workflow
"""

import os
from datetime import date, datetime
from dotenv import load_dotenv
from pathlib import Path
import argparse

# Import our modular components
from console_utils import (
    print_header, print_section, print_success, print_error, print_warning,
    print_info, print_data, print_json_preview, confirm_proceed,
    get_dataset_name_input, get_date_range_input, get_limit_input, Colors
)
from faen_client import FaenApiClient, create_full_day_query, create_weather_query
from cde_client import CDEApiClient
from data_utils import (
    generate_dataset_definition, save_dataset_definition,
    transform_faen_to_datapoints, generate_combined_dataset_definition,
    transform_generation_to_datapoints, transform_weather_to_datapoints
)

# Constants - default values (will be overridden by environment variables)
SAMPLE_RECORDS_DISPLAY = 2  # Number of sample records to show
MAX_USER_IDS_DISPLAY = 5    # Maximum number of user IDs to display
DEFAULT_BATCH_SIZE = 50     # Default batch size for datapoint uploads

# Global variable for non-interactive mode
NON_INTERACTIVE_MODE = False


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
    
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(
        description="FAEN API Client for Consumption Data with CDE Integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (default)
  python main.py
  
  # Non-interactive mode - consumption data only
  python main.py --dataset-type 1 --start-date 2025-05-01 --end-date 2025-05-02
  
  # Non-interactive mode - generation + weather data
  python main.py --dataset-type 2 --start-date 2025-05-01 --end-date 2025-05-02
  
  # Non-interactive mode - both dataset types
  python main.py --dataset-type 3 --start-date 2025-05-01 --end-date 2025-05-02
  
  # With custom record limit
  python main.py --dataset-type 1 --start-date 2025-05-01 --end-date 2025-05-02 --limit 100
        """
    )
    
    parser.add_argument(
        '--dataset-type', 
        type=int, 
        choices=[1, 2, 3],
        help='Dataset type: 1=Building Consumption, 2=Photovoltaic Generation, 3=Both types'
    )
    
    parser.add_argument(
        '--start-date', 
        type=str, 
        help='Start date in YYYY-MM-DD format (inclusive)'
    )
    
    parser.add_argument(
        '--end-date', 
        type=str, 
        help='End date in YYYY-MM-DD format (exclusive)'
    )
    
    parser.add_argument(
        '--limit', 
        type=int, 
        help='Maximum number of records to retrieve'
    )
    
    parser.add_argument(
        '--non-interactive', 
        action='store_true',
        help='Run in non-interactive mode (auto-confirm all prompts)'
    )
    
    args = parser.parse_args()
    
    # Set non-interactive mode flag
    global NON_INTERACTIVE_MODE
    NON_INTERACTIVE_MODE = args.non_interactive
    
    # Validate non-interactive mode arguments
    if args.non_interactive:
        if args.dataset_type is None:
            print_error("❌ --dataset-type is required in non-interactive mode")
            return
        if args.start_date is None:
            print_error("❌ --start-date is required in non-interactive mode")
            return
        if args.end_date is None:
            print_error("❌ --end-date is required in non-interactive mode")
            return
        
        # Validate date formats
        try:
            datetime.strptime(args.start_date, '%Y-%m-%d')
            datetime.strptime(args.end_date, '%Y-%m-%d')
        except ValueError:
            print_error("❌ Dates must be in YYYY-MM-DD format")
            return
    
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
        "CDE. Do you want to continue?", non_interactive=NON_INTERACTIVE_MODE
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
                "retrieval configuration?", non_interactive=NON_INTERACTIVE_MODE
            ):
                print_info("❌ Operation cancelled by user")
                return
            
            # Dataset type selection
            if args.dataset_type:
                # Non-interactive mode: use command line argument
                choice = str(args.dataset_type)
                print_info(f"🤖 [NON-INTERACTIVE] Using dataset type from command line: {choice}")
                create_consumption = choice in ['1', '3']
                create_generation = choice in ['2', '3']
            else:
                # Interactive mode: ask user
                print_section("📊 Dataset Type Selection")
                print_info("Available dataset types:")
                print_data("1", "Building Consumption (energy consumption data)", 1)
                print_data("2", "Photovoltaic Generation (generation + weather data)", 1)
                print_data("3", "Both types (creates separate datasets)", 1)
                
                while True:
                    try:
                        choice = input("\nSelect dataset type (1-3): ").strip()
                        if choice in ['1', '2', '3']:
                            break
                        print_warning("Please enter 1, 2, or 3")
                    except (EOFError, KeyboardInterrupt):
                        print_info("\n❌ Operation cancelled by user")
                        return
                
                create_consumption = choice in ['1', '3']
                create_generation = choice in ['2', '3']
            
            print_info(f"Selected: {'Consumption' if create_consumption else ''}{'Both' if create_consumption and create_generation else ''}{'Generation + Weather' if create_generation and not create_consumption else ''}")
            
            # Get user input for date range and limit
            start_date, end_date = get_date_range_input(args.start_date, args.end_date, NON_INTERACTIVE_MODE)
            limit = get_limit_input(DEFAULT_BATCH_SIZE if args.limit is None else 50, args.limit)
            
            print_section("📅 Final Configuration Summary")
            today = date.today()
            print_data("Today", str(today), 1)
            print_data("Query start date", f"{start_date} (00:00:00, inclusive)", 1)
            print_data(
                "Query end date",
                f"{end_date} (exclusive, up to 00:00:00)",
                1
            )
            total_days = (end_date - start_date).days
            print_data("Total days", f"{total_days} complete days", 1)
            print_data("Record limit", f"{limit} records maximum", 1)
            
            query = create_full_day_query(start_date, end_date)
            
            print_section("🔍 MongoDB Query")
            print_data("Query type", "Full day range query", 1)
            print_json_preview(query)
            
            # Initialize data containers
            consumption_data = []
            generation_data = []
            weather_data = []
            
            # Query data based on selection
            if create_consumption:
                print_section("🏢 Querying Consumption Data")
                consumption_data = faen_client.query_consumption(
                    query=query,
                    limit=limit,
                    sort="+datetime"
                )
                print_data("Consumption records", str(len(consumption_data)), 1)
            
            if create_generation:
                print_section("⚡ Querying Generation Data")
                generation_data = faen_client.query_generation(
                    query=query,
                    limit=limit,
                    sort="+datetime"
                )
                print_data("Generation records", str(len(generation_data)), 1)
                
                print_section("🌤️ Querying Weather Data")
                weather_query = create_weather_query(start_date, end_date)
                weather_data = faen_client.query_weather(
                    query=weather_query,
                    limit=limit,
                    sort="+datetime_utc"
                )
                print_data("Weather records", str(len(weather_data)), 1)
            
            print_section("📋 FAEN Results Summary")
            total_records = len(consumption_data) + len(generation_data) + len(weather_data)
            print_data("Total records retrieved", str(total_records), 1)
            if create_consumption:
                print_data("Consumption records", str(len(consumption_data)), 1)
            if create_generation:
                print_data("Generation records", str(len(generation_data)), 1)
                print_data("Weather records", str(len(weather_data)), 1)
            
            # Confirmation point 2: After data retrieval
            if not confirm_proceed(
                f"Retrieved {total_records} records from FAEN. Do you "
                f"want to continue with dataset generation?", non_interactive=NON_INTERACTIVE_MODE
            ):
                print_info("❌ Operation cancelled by user")
                return
            
            # Print first few records
            if consumption_data or generation_data or weather_data:
                print_section("📊 Sample FAEN Data")
                
                # Show consumption data samples
                if consumption_data:
                    print_info("Consumption Data Sample:")
                    for i, record in enumerate(consumption_data[:SAMPLE_RECORDS_DISPLAY]):
                        print(
                            f"\n{Colors.BOLD}{Colors.MAGENTA}  Consumption Record {i+1}:"
                            f"{Colors.RESET}"
                        )
                        print_json_preview(record)
                    
                    if len(consumption_data) > SAMPLE_RECORDS_DISPLAY:
                        remaining = len(consumption_data) - SAMPLE_RECORDS_DISPLAY
                        print(
                            f"\n{Colors.GRAY}  ... and {remaining} more consumption records"
                            f"{Colors.RESET}"
                        )
                
                # Show generation data samples
                if generation_data:
                    print_info("Generation Data Sample:")
                    for i, record in enumerate(generation_data[:SAMPLE_RECORDS_DISPLAY]):
                        print(
                            f"\n{Colors.BOLD}{Colors.MAGENTA}  Generation Record {i+1}:"
                            f"{Colors.RESET}"
                        )
                        print_json_preview(record)
                    
                    if len(generation_data) > SAMPLE_RECORDS_DISPLAY:
                        remaining = len(generation_data) - SAMPLE_RECORDS_DISPLAY
                        print(
                            f"\n{Colors.GRAY}  ... and {remaining} more generation records"
                            f"{Colors.RESET}"
                        )
                
                # Show weather data samples
                if weather_data:
                    print_info("Weather Data Sample:")
                    for i, record in enumerate(weather_data[:SAMPLE_RECORDS_DISPLAY]):
                        print(
                            f"\n{Colors.BOLD}{Colors.MAGENTA}  Weather Record {i+1}:"
                            f"{Colors.RESET}"
                        )
                        print_json_preview(record)
                    
                    if len(weather_data) > SAMPLE_RECORDS_DISPLAY:
                        remaining = len(weather_data) - SAMPLE_RECORDS_DISPLAY
                        print(
                            f"\n{Colors.GRAY}  ... and {remaining} more weather records"
                            f"{Colors.RESET}"
                        )
                
                # Generate dataset definitions based on selection
                datasets_to_process = []
                
                if create_consumption and consumption_data:
                    print_section("📋 Building Consumption Dataset Generation")
                    print_info("Generating consumption dataset definition...")
                    
                    consumption_dataset = generate_dataset_definition(
                        start_date, end_date, consumption_data
                    )
                    datasets_to_process.append({
                        'definition': consumption_dataset,
                        'type': 'consumption',
                        'data': consumption_data,
                        'name': 'Building Consumption Dataset'
                    })
                    
                    print_success("✓ Consumption dataset definition generated")
                    print_data("Dataset name", consumption_dataset.get('datacellar:name', 'Unknown'), 1)
                    timeseries_list = consumption_dataset.get('datacellar:timeSeries', [])
                    print_data("Number of timeseries", str(len(timeseries_list)), 1)
                
                if create_generation and generation_data and weather_data:
                    print_section("📋 Photovoltaic Generation Dataset Generation")
                    print_info("Generating combined generation + weather dataset definition...")
                    
                    generation_dataset = generate_combined_dataset_definition(
                        start_date, end_date, generation_data, weather_data
                    )
                    datasets_to_process.append({
                        'definition': generation_dataset,
                        'type': 'generation',
                        'data': {'generation': generation_data, 'weather': weather_data},
                        'name': 'Photovoltaic Generation Dataset'
                    })
                    
                    print_success("✓ Generation dataset definition generated")
                    print_data("Dataset name", generation_dataset.get('datacellar:name', 'Unknown'), 1)
                    timeseries_list = generation_dataset.get('datacellar:timeSeries', [])
                    print_data("Number of timeseries", str(len(timeseries_list)), 1)
                
                elif create_generation and (not generation_data or not weather_data):
                    print_warning("⚠ Cannot create generation dataset - insufficient data")
                    print_data("Generation records", str(len(generation_data)), 1)
                    print_data("Weather records", str(len(weather_data)), 1)
                
                if not datasets_to_process:
                    print_error("❌ No datasets can be generated with available data")
                    return
                
                print_section("📊 Dataset Summary")
                print_data("Total datasets to create", str(len(datasets_to_process)), 1)
                for i, dataset_info in enumerate(datasets_to_process, 1):
                    print_data(f"Dataset {i}", f"{dataset_info['name']} ({dataset_info['type']})", 1)
                
                # Process each dataset
                for dataset_info in datasets_to_process:
                    dataset_definition = dataset_info['definition']
                    dataset_type = dataset_info['type']
                    
                    print_section(f"📝 Processing {dataset_info['name']}")
                    
                    # Get custom dataset name from user
                    default_name = dataset_definition.get(
                        'datacellar:name', 'FAEN Dataset'
                    )
                    # In non-interactive mode, use default name
                    if NON_INTERACTIVE_MODE:
                        custom_name = default_name
                        print_info(f"🤖 [NON-INTERACTIVE] Using default dataset name: {custom_name}")
                    else:
                        custom_name = get_dataset_name_input(f"{default_name} ({dataset_type})")
                    
                    # Update dataset definition with custom name
                    if custom_name != default_name:
                        dataset_definition['datacellar:name'] = custom_name
                        print_info(f"Dataset name updated to: {custom_name}")
                    
                    # Confirmation point 3: After dataset generation and naming
                    if not confirm_proceed(
                        f"Dataset definition ready for {dataset_type}. Do you want to save it to file?", non_interactive=NON_INTERACTIVE_MODE
                    ):
                        print_info("❌ Operation cancelled by user")
                        continue
                    
                    # Save dataset definition to filesystem
                    print_section(f"💾 Saving {dataset_type.title()} Dataset Definition")
                    dataset_file_path = save_dataset_definition(
                        dataset_definition, start_date, end_date, dataset_type
                    )
                    
                    # Store file path for later processing
                    dataset_info['file_path'] = dataset_file_path
                
                # Process CDE uploads
                if not confirm_proceed(
                    f"All dataset definitions saved. Do you want to upload them to CDE?", non_interactive=NON_INTERACTIVE_MODE
                ):
                    print_info("❌ CDE upload cancelled by user")
                    print_info("💡 Dataset files saved locally for manual upload when ready")
                    return
                
                # Upload datasets to CDE
                print_section("⬆️ Uploading Datasets to CDE")
                
                successful_uploads = []
                
                for dataset_info in datasets_to_process:
                    if 'file_path' not in dataset_info:
                        continue
                        
                    dataset_definition = dataset_info['definition']
                    dataset_type = dataset_info['type']
                    dataset_file_path = dataset_info['file_path']
                    
                    print_info(f"Uploading {dataset_type} dataset...")
                    
                    upload_result = cde_client.upload_dataset(dataset_file_path)
                    
                    if upload_result:
                        print_success(f"✓ {dataset_type.title()} dataset uploaded successfully")
                        
                        # Extract dataset ID from the response
                        dataset_id = upload_result.get('dataset_id')
                        if dataset_id:
                            print_data(f"{dataset_type.title()} Dataset ID", dataset_id, 1)
                        
                        dataset_info['upload_result'] = upload_result
                        dataset_info['dataset_id'] = dataset_id
                        successful_uploads.append(dataset_info)
                    else:
                        print_error(f"✗ Failed to upload {dataset_type} dataset")
                
                if not successful_uploads:
                    print_error("❌ No datasets were successfully uploaded")
                    return
                
                # Confirmation point 5: Before datapoint upload
                if not confirm_proceed(
                    f"{len(successful_uploads)} dataset(s) uploaded successfully. Do you want to "
                    "proceed with uploading datapoints?", non_interactive=NON_INTERACTIVE_MODE
                ):
                    print_info("❌ Datapoint upload cancelled by user")
                    print_info("💡 Datasets are available in CDE, datapoints can be uploaded separately")
                    return
                
                # Upload datapoints for each successful dataset
                print_section("📊 Uploading Datapoints to CDE")
                
                for dataset_info in successful_uploads:
                    dataset_type = dataset_info['type']
                    dataset_definition = dataset_info['definition']
                    dataset_id = dataset_info['dataset_id']
                    dataset_name = dataset_definition.get('datacellar:name', '')
                    
                    print_info(f"Processing datapoints for {dataset_type} dataset...")
                    
                    # Get timeseries from CDE
                    timeseries_list = cde_client.get_timeseries(
                        dataset_id=dataset_id, dataset_name=dataset_name
                    )
                    
                    if not timeseries_list:
                        print_error(f"✗ Failed to retrieve timeseries for {dataset_type} dataset")
                        continue
                    
                    print_info(f"Retrieved {len(timeseries_list)} timeseries from CDE")
                    
                    # Process datapoints based on dataset type
                    if dataset_type == 'consumption':
                        # Create mapping and transform consumption data
                        timeseries_mapping = {}
                        for ts in timeseries_list:
                            metadata = ts.get('timeSeriesMetadata', {})
                            device_id = metadata.get('datacellar:deviceID')
                            ts_id = ts.get('id')
                            if device_id and ts_id:
                                timeseries_mapping[str(device_id)] = ts_id
                        
                        if timeseries_mapping:
                            datapoints = transform_faen_to_datapoints(
                                dataset_info['data'], timeseries_mapping
                            )
                        else:
                            datapoints = []
                    
                    elif dataset_type == 'generation':
                        # Create mapping using datasetField information from CDE
                        timeseries_mapping = {}
                        
                        for ts in timeseries_list:
                            dataset_field = ts.get('datasetField', {})
                            field_id = dataset_field.get('datacellar:datasetFieldID')
                            field_name = dataset_field.get('datacellar:name')
                            ts_id = ts.get('id')
                            
                            print_info(f"Processing timeseries {ts_id}:")
                            print_data("Field ID", str(field_id), 2)
                            print_data("Field Name", str(field_name), 2)
                            
                            if not field_id or not ts_id:
                                print_warning(f"⚠ Missing field ID or timeseries ID for {ts_id}")
                                continue
                            
                            # Map by field ID (handle both string and integer)
                            field_id_str = str(field_id)
                            mapped = False
                            
                            if field_id_str == "1":
                                timeseries_mapping['generation'] = ts_id
                                print_data("Mapped to", "generation (by ID)", 2)
                                mapped = True
                            elif field_id_str == "2":
                                timeseries_mapping['outdoorTemperature'] = ts_id
                                print_data("Mapped to", "outdoorTemperature (by ID)", 2)
                                mapped = True
                            elif field_id_str == "3":
                                timeseries_mapping['humidity'] = ts_id
                                print_data("Mapped to", "humidity (by ID)", 2)
                                mapped = True
                            
                            # Fallback: try mapping by field name
                            if not mapped and field_name:
                                if field_name == "generatedEnergy":
                                    timeseries_mapping['generation'] = ts_id
                                    print_data("Mapped to", "generation (by name)", 2)
                                    mapped = True
                                elif field_name == "outdoorTemperature":
                                    timeseries_mapping['outdoorTemperature'] = ts_id
                                    print_data("Mapped to", "outdoorTemperature (by name)", 2)
                                    mapped = True
                                elif field_name == "humidityLevel":
                                    timeseries_mapping['humidity'] = ts_id
                                    print_data("Mapped to", "humidity (by name)", 2)
                                    mapped = True
                            
                            if not mapped:
                                print_warning(f"⚠ Could not map timeseries {ts_id} (ID: {field_id}, Name: {field_name})")
                        
                        print_info(f"Final timeseries mapping: {timeseries_mapping}")
                        
                        # Validate we have all required mappings
                        expected_mappings = ['generation', 'outdoorTemperature', 'humidity']
                        missing_mappings = [m for m in expected_mappings if m not in timeseries_mapping]
                        if missing_mappings:
                            print_warning(f"⚠ Missing mappings for: {', '.join(missing_mappings)}")
                        
                        if timeseries_mapping:
                            # Transform generation data
                            generation_datapoints = transform_generation_to_datapoints(
                                dataset_info['data']['generation'], timeseries_mapping
                            )
                            # Transform weather data
                            weather_datapoints = transform_weather_to_datapoints(
                                dataset_info['data']['weather'], 
                                timeseries_mapping.get('outdoorTemperature'),
                                timeseries_mapping.get('humidity')
                            )
                            datapoints = generation_datapoints + weather_datapoints
                        else:
                            datapoints = []
                    
                    if datapoints:
                        # Upload datapoints in batches
                        batch_result = cde_client.add_datapoints_batch(
                            datapoints, batch_size=DEFAULT_BATCH_SIZE
                        )
                        
                        print_info(f"Datapoint upload results for {dataset_type}:")
                        print_data("Total datapoints", str(batch_result['total']), 2)
                        print_data("Successfully uploaded", str(batch_result['success']), 2)
                        print_data("Failed uploads", str(batch_result['failed']), 2)
                        
                        if batch_result['success'] > 0:
                            success_rate = (batch_result['success'] / batch_result['total']) * 100
                            print_data("Success rate", f"{success_rate:.1f}%", 2)
                        
                        dataset_info['datapoint_result'] = batch_result
                    else:
                        print_warning(f"⚠ No valid datapoints generated for {dataset_type} dataset")
                
                
                # Final summary
                print_header("✅ FAEN ➔ CDE Integration Completed")
                
                # Data retrieval summary
                print_success(f"✓ Successfully retrieved {total_records} FAEN records")
                if create_consumption:
                    print_success(f"  • {len(consumption_data)} consumption records")
                if create_generation:
                    print_success(f"  • {len(generation_data)} generation records")
                    print_success(f"  • {len(weather_data)} weather records")
                
                # Dataset generation summary
                if datasets_to_process:
                    print_success(f"✓ Successfully generated {len(datasets_to_process)} dataset definition(s)")
                    for dataset_info in datasets_to_process:
                        if 'file_path' in dataset_info:
                            print_success(f"  • {dataset_info['name']} saved to: {dataset_info['file_path']}")
                
                # Upload summary
                if successful_uploads:
                    print_success(f"✓ Successfully uploaded {len(successful_uploads)} dataset(s) to CDE")
                    
                    total_datapoints_uploaded = 0
                    total_datapoints_failed = 0
                    
                    for dataset_info in successful_uploads:
                        dataset_type = dataset_info['type']
                        if 'datapoint_result' in dataset_info:
                            result = dataset_info['datapoint_result']
                            success_count = result['success']
                            failed_count = result['failed']
                            total_datapoints_uploaded += success_count
                            total_datapoints_failed += failed_count
                            
                            print_success(f"  • {dataset_type.title()}: {success_count} datapoints uploaded")
                            if failed_count > 0:
                                print_warning(f"    ⚠ {failed_count} datapoints failed")
                    
                    if total_datapoints_uploaded > 0:
                        print_success(f"✓ Total datapoints uploaded: {total_datapoints_uploaded}")
                        
                        if total_datapoints_failed == 0:
                            print_info("🎉 Complete integration pipeline executed successfully!")
                        else:
                            print_info(f"⚠ Integration completed with {total_datapoints_failed} datapoint upload failures")
                    else:
                        print_warning("⚠ Datasets uploaded but no datapoints were successfully added")
                else:
                    print_info("📁 Dataset files ready for manual upload to CDE when available")
                    
            else:
                print_warning("⚠ No data found for the specified date range")
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