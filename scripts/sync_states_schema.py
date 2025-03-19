#!/usr/bin/env python

"""Script to synchronize states field in schema.json files with Config classes."""

import ast
import json
from pathlib import Path
from typing import Optional, Set

# Root directory of the project
ROOT_DIR = Path(__file__).parent.parent
SKILLS_DIR = ROOT_DIR / "skills"


def get_skill_states_from_file(skill_dir: Path) -> Optional[Set[str]]:
    """Extract state names from the SkillStates class in __init__.py.

    Args:
        skill_dir: The directory of the skill

    Returns:
        A set of state names if found, None otherwise
    """
    init_file = skill_dir / "__init__.py"
    if not init_file.exists():
        print(f"No __init__.py found in {skill_dir}")
        return None
    
    try:
        # Read the file content
        with open(init_file, "r") as f:
            content = f.read()
        
        # Parse the file into an AST
        tree = ast.parse(content)
        
        # Find the SkillStates class
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "SkillStates":
                # Look for annotations in the class
                states = set()
                for child in node.body:
                    if isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
                        states.add(child.target.id)
                return states
        
        print(f"No SkillStates class found in {init_file}")
        return None
    except Exception as e:
        print(f"Error parsing {init_file}: {e}")
        return None


def update_states_schema(schema_path: Path) -> None:
    """Update the states field in schema.json files based on SkillStates class.

    Args:
        schema_path: The path to the schema.json file
    """
    # Check if schema.json exists
    if not schema_path.exists():
        print(f"No schema.json found at {schema_path}")
        return
    
    # Get the skill directory
    skill_dir = schema_path.parent
    skill_name = skill_dir.name
    
    # Get the state names from the SkillStates class
    class_states = get_skill_states_from_file(skill_dir)
    if not class_states:
        print(f"No states found for {skill_name}")
        return
    
    # Load the existing schema
    with open(schema_path, "r") as f:
        schema = json.load(f)
    
    changes_made = False
    
    # Check if 'states' field exists in the schema
    if "states" not in schema.get("properties", {}):
        # Add the states field
        if "properties" not in schema:
            schema["properties"] = {}
        
        schema["properties"]["states"] = {
            "type": "object",
            "properties": {},
            "description": f"States for each {skill_name.capitalize()} skill (disabled, public, or private)"
        }
        changes_made = True
    
    states_schema = schema["properties"]["states"]
    
    # Ensure states has the correct structure
    if "type" not in states_schema:
        states_schema["type"] = "object"
        changes_made = True
    
    if "description" not in states_schema:
        states_schema["description"] = f"States for each {skill_name.capitalize()} skill (disabled, public, or private)"
        changes_made = True
    
    # Ensure properties exists in states
    if "properties" not in states_schema:
        states_schema["properties"] = {}
        changes_made = True
    
    # Add missing states from the class to the schema
    for state_name in class_states:
        if state_name not in states_schema["properties"]:
            # Add the state to the schema
            states_schema["properties"][state_name] = {
                "type": "string",
                "title": " ".join(word.capitalize() for word in state_name.split("_")),
                "enum": ["disabled", "public", "private"],
                "description": f"State for {state_name}",
                "default": "disabled"
            }
            changes_made = True
            print(f"Added state '{state_name}' to {schema_path}")
        else:
            # Update existing state
            state_props = states_schema["properties"][state_name]
            
            # Ensure enum values are correct
            if "enum" not in state_props or set(state_props["enum"]) != {"disabled", "public", "private"}:
                state_props["enum"] = ["disabled", "public", "private"]
                changes_made = True
            
            # Add or update default value to "disabled"
            if "default" not in state_props or state_props["default"] != "disabled":
                state_props["default"] = "disabled"
                changes_made = True
    
    # Save the updated schema if changes were made
    if changes_made:
        with open(schema_path, "w") as f:
            json.dump(schema, f, indent=2)
        
        print(f"Updated states schema at {schema_path}")
    else:
        print(f"No changes needed for {schema_path}")


def main():
    """Main function to synchronize all schema.json files."""
    # Find all schema.json files in the skills directory
    schema_files = list(SKILLS_DIR.glob("*/schema.json"))
    
    for schema_path in schema_files:
        update_states_schema(schema_path)


if __name__ == "__main__":
    main()
