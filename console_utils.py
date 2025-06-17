#!/usr/bin/env python3
"""
Console utilities for colored output and user input handling
"""

import json
from datetime import datetime, timedelta, date
from typing import Dict, Any


class Colors:
    """ANSI color codes for terminal output"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # Colors
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'
    
    # Background colors
    BG_RED = '\033[101m'
    BG_GREEN = '\033[102m'
    BG_YELLOW = '\033[103m'
    BG_BLUE = '\033[104m'


def print_header(title: str):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}  {title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}\n")


def print_section(title: str):
    """Print a section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}▶ {title}{Colors.RESET}")
    print(f"{Colors.GRAY}{'─'*50}{Colors.RESET}")


def print_success(message: str):
    """Print a success message"""
    print(f"{Colors.GREEN}{message}{Colors.RESET}")


def print_error(message: str):
    """Print an error message"""
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")


def print_warning(message: str):
    """Print a warning message"""
    print(f"{Colors.YELLOW}{message}{Colors.RESET}")


def print_info(message: str):
    """Print an info message"""
    print(f"{Colors.CYAN}ℹ {message}{Colors.RESET}")


def print_data(label: str, value: str, indent: int = 0):
    """Print labeled data"""
    spaces = "  " * indent
    print(f"{spaces}{Colors.GRAY}{label}:{Colors.RESET} {Colors.WHITE}{value}{Colors.RESET}")


def print_json_preview(data: Dict[str, Any], max_items: int = 3):
    """Print a formatted JSON preview"""
    if not data:
        print(f"{Colors.GRAY}  (No data to display){Colors.RESET}")
        return
    
    print(f"{Colors.BOLD}{Colors.MAGENTA}  📄 Data Preview:{Colors.RESET}")
    formatted = json.dumps(data, indent=2, ensure_ascii=False)
    lines = formatted.split('\n')
    
    # Show first few lines
    for i, line in enumerate(lines[:15]):  # Show first 15 lines
        if i < 14 or i == len(lines) - 1:
            print(f"{Colors.GRAY}    {line}{Colors.RESET}")
        elif i == 14 and len(lines) > 15:
            print(f"{Colors.GRAY}    ... ({len(lines) - 15} more lines){Colors.RESET}")
            break


def confirm_proceed(message: str, default: bool = True) -> bool:
    """
    Ask user for confirmation to proceed
    
    Args:
        message: Message to display to user
        default: Default choice if user just presses Enter
        
    Returns:
        True if user wants to proceed, False otherwise
    """
    default_text = "Y/n" if default else "y/N"
    while True:
        try:
            response = input(f"\n{Colors.BOLD}{Colors.CYAN}🤔 {message} ({default_text}): {Colors.RESET}").strip().lower()
            
            if not response:  # User pressed Enter without typing
                return default
            elif response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print_warning("Please enter 'y' for yes or 'n' for no (or just press Enter for default)")
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Operation cancelled by user{Colors.RESET}")
            return False
        except EOFError:
            return default


def get_dataset_name_input(default_name: str) -> str:
    """
    Get dataset name from user input with default fallback
    
    Args:
        default_name: Default dataset name to use if user just presses Enter
        
    Returns:
        User's chosen dataset name or default if no input provided
    """
    print(f"\n{Colors.BOLD}{Colors.BLUE}📝 Dataset Name Configuration{Colors.RESET}")
    print(f"{Colors.GRAY}{'─'*50}{Colors.RESET}")
    print_data("Current dataset name", default_name, 1)
    
    try:
        user_input = input(f"\n{Colors.BOLD}{Colors.CYAN}✏️  Enter a custom dataset name (or press Enter to keep default): {Colors.RESET}").strip()
        
        if not user_input:  # User pressed Enter without typing
            print_success(f"✓ Using default dataset name: {default_name}")
            return default_name
        else:
            print_success(f"✓ Using custom dataset name: {user_input}")
            return user_input
            
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Input cancelled by user, using default name{Colors.RESET}")
        return default_name
    except EOFError:
        return default_name


def get_date_range_input() -> tuple[date, date]:
    """
    Get start and end dates from user input with default fallback
    
    Returns:
        Tuple of (start_date, end_date) as date objects
    """
    print(f"\n{Colors.BOLD}{Colors.BLUE}📅 Date Range Configuration{Colors.RESET}")
    print(f"{Colors.GRAY}{'─'*50}{Colors.RESET}")
    
    # Calculate defaults (last 7 full days)
    today = date.today()
    default_end_date = today - timedelta(days=1)  # Yesterday
    default_start_date = default_end_date - timedelta(days=6)  # 7 days total
    
    print_data("Default start date", f"{default_start_date} (7 days ago)", 1)
    print_data("Default end date", f"{default_end_date} (yesterday)", 1)
    print_data("Default range", "7 complete days", 1)
    
    try:
        # Get start date
        start_input = input(f"\n{Colors.BOLD}{Colors.CYAN}📅 Enter start date (YYYY-MM-DD format, or press Enter for default): {Colors.RESET}").strip()
        
        if not start_input:
            start_date = default_start_date
            print_success(f"✓ Using default start date: {start_date}")
        else:
            try:
                start_date = datetime.strptime(start_input, '%Y-%m-%d').date()
                print_success(f"✓ Using custom start date: {start_date}")
            except ValueError:
                print_warning(f"⚠ Invalid date format '{start_input}', using default")
                start_date = default_start_date
        
        # Get end date
        end_input = input(f"\n{Colors.BOLD}{Colors.CYAN}📅 Enter end date (YYYY-MM-DD format, or press Enter for default): {Colors.RESET}").strip()
        
        if not end_input:
            end_date = default_end_date
            print_success(f"✓ Using default end date: {end_date}")
        else:
            try:
                end_date = datetime.strptime(end_input, '%Y-%m-%d').date()
                print_success(f"✓ Using custom end date: {end_date}")
            except ValueError:
                print_warning(f"⚠ Invalid date format '{end_input}', using default")
                end_date = default_end_date
        
        # Validate date range
        if start_date > end_date:
            print_warning("⚠ Start date is after end date, swapping them")
            start_date, end_date = end_date, start_date
        
        # Calculate and display the range
        date_range = (end_date - start_date).days + 1
        print_info(f"📊 Selected date range: {date_range} days ({start_date} to {end_date})")
        
        return start_date, end_date
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Input cancelled by user, using defaults{Colors.RESET}")
        return default_start_date, default_end_date
    except EOFError:
        return default_start_date, default_end_date


def get_limit_input(default_limit: int = 50) -> int:
    """
    Get record limit from user input with default fallback
    
    Args:
        default_limit: Default limit to use if user just presses Enter
        
    Returns:
        User's chosen limit or default if no input provided
    """
    print(f"\n{Colors.BOLD}{Colors.BLUE}🔢 Record Limit Configuration{Colors.RESET}")
    print(f"{Colors.GRAY}{'─'*50}{Colors.RESET}")
    print_data("Default limit", f"{default_limit} records", 1)
    print_info("💡 Higher limits may take longer to process and upload")
    
    try:
        user_input = input(f"\n{Colors.BOLD}{Colors.CYAN}🔢 Enter maximum number of records to retrieve (or press Enter for default): {Colors.RESET}").strip()
        
        if not user_input:  # User pressed Enter without typing
            print_success(f"✓ Using default limit: {default_limit} records")
            return default_limit
        else:
            try:
                limit = int(user_input)
                if limit <= 0:
                    print_warning("⚠ Limit must be positive, using default")
                    return default_limit
                elif limit > 1000:
                    print_warning("⚠ Large limits may cause performance issues")
                    confirm = input(f"{Colors.YELLOW}Continue with {limit} records? (y/N): {Colors.RESET}").strip().lower()
                    if confirm not in ['y', 'yes']:
                        print_info("Using default limit instead")
                        return default_limit
                
                print_success(f"✓ Using custom limit: {limit} records")
                return limit
                
            except ValueError:
                print_warning(f"⚠ Invalid number '{user_input}', using default")
                return default_limit
            
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Input cancelled by user, using default limit{Colors.RESET}")
        return default_limit
    except EOFError:
        return default_limit