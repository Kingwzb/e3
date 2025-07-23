#!/usr/bin/env python3
"""
Schema File Updater

This script updates the Python schema file from a generated text schema file.
"""

import os
import sys
from datetime import datetime


def update_python_schema_file(text_file_path: str, python_file_path: str = "schemas/unified_schema.py") -> bool:
    """Update the Python schema file from a text schema file."""
    try:
        # Check if text file exists
        if not os.path.exists(text_file_path):
            print(f"❌ Text schema file not found: {text_file_path}")
            return False
        
        # Read the text schema file
        print(f"📖 Reading schema from: {text_file_path}")
        with open(text_file_path, 'r', encoding='utf-8') as f:
            schema_content = f.read()
        
        # Generate the Python file content
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        python_content = f'''"""
Unified schema document for the MongoDB database.
This schema provides a comprehensive view of all collections, their relationships, 
field definitions, and supplementary explanations.
Generated on: {timestamp}
"""

UNIFIED_SCHEMA = """{schema_content}"""
'''
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(python_file_path), exist_ok=True)
        
        # Write the Python file
        with open(python_file_path, 'w', encoding='utf-8') as f:
            f.write(python_content)
        
        print(f"✅ Python schema file updated: {python_file_path}")
        print(f"📄 File size: {len(python_content)} characters")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to update Python schema file: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python update_schema_from_file.py <text_schema_file> [python_schema_file]")
        print("Example: python update_schema_from_file.py schemas/unified_schema.txt")
        sys.exit(1)
    
    text_file = sys.argv[1]
    python_file = sys.argv[2] if len(sys.argv) > 2 else "schemas/unified_schema.py"
    
    success = update_python_schema_file(text_file, python_file)
    
    if success:
        print(f"\n🎉 Schema update completed successfully!")
    else:
        print(f"\n❌ Schema update failed!")
        sys.exit(1)


if __name__ == "__main__":
    main() 