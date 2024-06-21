import logging
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
import inspect

BASE_DIR = Path(__file__).resolve().parent.parent

def create_dated_log_file(log_name):
    """
    Creates a log file with a date-based name if it doesn't exist.

    Args:
        log_name (str): The base name for the log file.

    Returns:
        str: The absolute path to the created log file, or None if creation fails.
    """
    today = datetime.now(timezone(timedelta(hours=3))).strftime('%Y-%m-%d')
    log_file = os.path.join(BASE_DIR, 'logs', f'{log_name}_{today}.log')

    try:
        if not os.path.exists(log_file):
            with open(log_file, 'w') as f:
                pass  # Create the empty file
    except OSError as e:
        print(f"Error creating log file: {e}")
        return None

    return log_file

def track_user_activity(username, action=None, log_name='user_activity'):
    """
    Tracks user activities and writes them to a date-based log file.

    Args:
        username (str): The username of the user performing the action.
        action (str, optional): The action the user performed (defaults to the view function name).
        log_name (str, optional): The base name for the log file. Defaults to 'user_activity'.
    """
    log_file = create_dated_log_file(log_name)

    if log_file:
        if not action:
            current_frame = inspect.currentframe()
            calling_frame = current_frame.f_back
            action = calling_frame.f_code.co_name

        # Create a custom logger
        logger = logging.getLogger(log_name)

        # Remove any existing handlers associated with the logger
        if logger.hasHandlers():
            logger.handlers.clear()

        # Create a file handler
        file_handler = logging.FileHandler(log_file)

        # Create a logging format
        formatter = logging.Formatter('%(message)s')
        file_handler.setFormatter(formatter)

        # Add the file handler to the logger
        logger.addHandler(file_handler)

        # Set the logging level
        logger.setLevel(logging.INFO)

        # Log the message with GMT+3 timezone
        now = datetime.now(timezone(timedelta(hours=3)))
        message = f"{now:%Y-%m-%d %H:%M:%S (%Z)} - user with username: '{username}' {action}"
        logger.info(message)
    else:
        print("Failed to create log file. User activity not logged.")
