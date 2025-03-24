"""
Migration package for database schema migrations.
This package contains all the database migrations that are run in sequence.
"""
import os
import importlib
from typing import List, Dict, Any

# Import all migration modules
def get_migration_modules() -> List[Dict[str, Any]]:
    """
    Load all migration modules in this package.
    
    Returns:
        List of dictionaries with 'name' and 'module' keys.
    """
    migrations = []
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Get all Python files in this directory
    files = sorted([
        f for f in os.listdir(current_dir) 
        if f.endswith('.py') and f != '__init__.py'
    ])
    
    # Import each module
    for file in files:
        module_name = file[:-3]  # Remove .py extension
        full_module_name = f"server.database.migrations.{module_name}"
        try:
            module = importlib.import_module(full_module_name)
            migrations.append({
                'name': module_name,
                'module': module
            })
        except Exception as e:
            print(f"Error importing migration module {module_name}: {str(e)}")
    
    return migrations
