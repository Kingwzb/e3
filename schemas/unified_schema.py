"""
Dynamic unified schema loader for MongoDB database schemas.
This module loads the schema from a text file and provides it as a Python variable.
"""

import os
import sys
from pathlib import Path


def load_unified_schema(schema_file_path: str = None) -> str:
    """
    Load the unified schema from a text file.
    
    Args:
        schema_file_path: Path to the schema text file. If None, uses default location.
    
    Returns:
        The schema content as a string.
    
    Raises:
        FileNotFoundError: If the schema file doesn't exist.
        Exception: For other file reading errors.
    """
    if schema_file_path is None:
        # Default to the text file in the same directory
        current_dir = Path(__file__).parent
        schema_file_path = current_dir / "unified_schema.txt"
    
    try:
        with open(schema_file_path, 'r', encoding='utf-8') as f:
            schema_content = f.read()
        return schema_content
    except FileNotFoundError:
        raise FileNotFoundError(f"Schema file not found: {schema_file_path}")
    except Exception as e:
        raise Exception(f"Error reading schema file: {e}")


def get_schema_file_path() -> str:
    """
    Get the default path to the schema text file.
    
    Returns:
        Path to the schema file.
    """
    current_dir = Path(__file__).parent
    return str(current_dir / "unified_schema.txt")


# Load the schema when the module is imported
try:
    UNIFIED_SCHEMA = load_unified_schema()
    SCHEMA_LOADED = True
    SCHEMA_FILE_PATH = get_schema_file_path()
except Exception as e:
    # Fallback to empty schema if file doesn't exist
    UNIFIED_SCHEMA = f"# Schema file not found or could not be loaded\n# Error: {e}\n# Please run the schema extraction tool to generate the schema file."
    SCHEMA_LOADED = False
    SCHEMA_FILE_PATH = get_schema_file_path()


def reload_schema() -> bool:
    """
    Reload the schema from the file.
    
    Returns:
        True if successful, False otherwise.
    """
    global UNIFIED_SCHEMA, SCHEMA_LOADED
    try:
        UNIFIED_SCHEMA = load_unified_schema()
        SCHEMA_LOADED = True
        return True
    except Exception as e:
        print(f"Warning: Could not reload schema: {e}")
        SCHEMA_LOADED = False
        return False


def get_schema_status() -> dict:
    """
    Get the current status of the schema loading.
    
    Returns:
        Dictionary with schema status information.
    """
    return {
        "loaded": SCHEMA_LOADED,
        "file_path": SCHEMA_FILE_PATH,
        "schema_length": len(UNIFIED_SCHEMA),
        "file_exists": os.path.exists(SCHEMA_FILE_PATH)
    }


# Example usage and documentation
if __name__ == "__main__":
    print("Unified Schema Loader")
    print("=" * 30)
    
    status = get_schema_status()
    print(f"Schema loaded: {status['loaded']}")
    print(f"File path: {status['file_path']}")
    print(f"File exists: {status['file_exists']}")
    print(f"Schema length: {status['schema_length']} characters")
    
    if not status['loaded']:
        print("\nTo generate the schema file, run:")
        print("python extract_and_update_schema.py --connection-string 'mongodb://localhost:27017' --database 'your_database'") 