#!/usr/bin/env python

"""Script to synchronize schema.json files with their corresponding Config classes."""

import json
from pathlib import Path

# Root directory of the project
ROOT_DIR = Path(__file__).parent.parent
SKILLS_DIR = ROOT_DIR / "skills"


def update_schema_json(schema_path: Path) -> None:
    """Update the schema.json file to include the 'enabled' field.

    Args:
        schema_path: The path to the schema.json file
    """
    # Check if schema.json exists
    if not schema_path.exists():
        print(f"No schema.json found at {schema_path}")
        return
    
    # Load the existing schema
    with open(schema_path, "r") as f:
        schema = json.load(f)
    
    # Check if 'enabled' field is already in the schema
    if "enabled" not in schema.get("properties", {}):
        # Add the 'enabled' field to the schema properties
        if "properties" not in schema:
            schema["properties"] = {}
        
        schema["properties"]["enabled"] = {
            "type": "boolean",
            "title": "Enabled",
            "description": "Whether this skill is enabled",
            "default": True
        }
        
        # Update the required fields if it exists
        if "required" in schema and "enabled" not in schema["required"]:
            schema["required"].append("enabled")
        elif "required" not in schema:
            schema["required"] = ["enabled"]
        
        # Save the updated schema
        with open(schema_path, "w") as f:
            json.dump(schema, f, indent=2)
        
        print(f"Updated schema.json at {schema_path}")
    else:
        print(f"'enabled' field already exists in {schema_path}")


def main():
    """Main function to synchronize all schema.json files."""
    # Find all schema.json files in the skills directory
    schema_files = list(SKILLS_DIR.glob("*/schema.json"))
    
    for schema_path in schema_files:
        update_schema_json(schema_path)


if __name__ == "__main__":
    main()
