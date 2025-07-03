# tests/frodo/test_import_variables.py
import pytest
from pathlib import Path
import json

from core.frodo.sync_esv import import_variables_to_cloud, delete_variables_to_cloud
from models.esv_models import EsvVariablePerEnv

# Load envs.json
CONFIG_PATH = Path(__file__).parent.parent / "envs.json"

with open(CONFIG_PATH) as f:
    TEST_ENVS = json.load(f)

def test_import_variables_to_cloud():
    env_name = "SBX"

    # Get SBX env details
    env = TEST_ENVS[env_name]
    
    # Example variable to import
    test_var_name = "esv-test123"
    test_var = EsvVariablePerEnv(
        description="Test variable for SBX123123",
        expressionType="string",
        value="5000"
    )
    
    # Build input dict
    variables_to_import = {
        test_var_name: test_var
    }

    env_data = {
    "frodo_path": env["frodo"],
    "platform_url": env["platformUrl"],
    "proxy": env.get("proxy")
    }
    
    # Call helper
    success = import_variables_to_cloud(
        env_name=env_name,
        env_data=env_data,
        variables=variables_to_import
    )
    
    assert success is True

def test_delete_variables_to_cloud():

    env_name = "SBX"

    # Get SBX env details
    env = TEST_ENVS[env_name]

    # Example variable to delete
    test_var_name = "esv-test123"
    test_var = EsvVariablePerEnv(
        description="Dummy",
        expressionType="string",
        value="Dummy"
    )

    # Build input dict
    variables_to_delete = {
        test_var_name: test_var
    }

    env_data = {
        "frodo_path": env["frodo"],
        "platform_url": env["platformUrl"],
        "proxy": env.get("proxy")
    }

    # Call helper
    success = delete_variables_to_cloud(
        env_name=env_name,
        env_data=env_data,
        variables=variables_to_delete
    )

    assert success is True