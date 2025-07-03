# core/frodo/sync_esv.py
from typing import Dict
import os

from models.esv_models import EsvVariablePerEnv
from core.logger import get_logger
from core.settings import settings
from core.frodo.utils import run_command, write_tempfile, load_json

logger = get_logger("__name__")

def pull_variables_for_env(env_name: str) -> Dict[str, EsvVariablePerEnv]:
    """Retrieve ESV variables for the given env from the authoritative source."""
    return pull_variables_from_local(env_name)

def add_variables_for_env(
    env_name: str,
    env_data: Dict,
    variables: Dict[str, EsvVariablePerEnv],
) -> bool:
    """Wrapper for adding new variables to the cloud for a given env."""
    logger.info(f"Adding variables for env: {env_name}")
    return import_variables_to_cloud(env_name, env_data, variables)

def update_variables_for_env(
    env_name: str,
    env_data: Dict,
    variables: Dict[str, EsvVariablePerEnv],
) -> bool:
    """Wrapper for updating existing variables to the cloud for a given env."""
    logger.info(f"Updating variables for env: {env_name}")
    return import_variables_to_cloud(env_name, env_data, variables)

def delete_variables_for_env(
    env_name: str,
    env_data: Dict,
    variables: Dict[str, EsvVariablePerEnv],
) -> bool:
    """Wrapper for deleting variables from the cloud for a given env."""
    logger.info(f"Deleting variables for env: {env_name}")
    return delete_variables_to_cloud(env_name, env_data, variables)

def pull_variables_from_local(
    env_name: str,
    paic_config_path: str = settings.PAIC_CONFIG_PATH
) -> Dict[str, EsvVariablePerEnv]:
    """
    Pull ESV variable data for given env from local repo.
    Reads JSON files in: configs/<ENV>/global/variable/
    """
    variable_dir = os.path.join(paic_config_path, "configs", env_name, "global", "variable")
    if not os.path.isdir(variable_dir):
        logger.error(f"Variable folder does not exist: {variable_dir}")
        raise FileNotFoundError(f"Variable folder not found: {variable_dir}")

    logger.info(f"Reading variables from: {variable_dir}")

    variables = {}

    for filename in os.listdir(variable_dir):
        if filename.endswith(".variable.json"):
            file_path = os.path.join(variable_dir, filename)
            logger.info(f"Processing variable file: {file_path}")
            data = load_json(file_path)
            if not data:
                logger.warning(f"Variable file is empty or invalid JSON: {file_path}")
                continue

            var_data = data.get("variable", {})
            if not var_data:
                logger.warning(f"No variables found in file: {filename}")
                continue
            logger.info(f"Found {len(var_data)} variables in file: {filename}")
            for var_name, var_content in var_data.items():
                variables[var_name] = EsvVariablePerEnv(
                    description=var_content.get("description", ""),
                    expressionType=var_content.get("expressionType", "string"),
                    value=var_content.get("value", "")
                )

    logger.info(f"Total variables collected: {len(variables)}")
    return variables

def import_variables_to_cloud(
    env_name: str,
    env_data: Dict,
    variables: Dict[str, EsvVariablePerEnv],
    paic_config_path: str = settings.PAIC_CONFIG_PATH
) -> bool:
    """
    Import (create/update) ESV variables for a specific env using frodo CLI.

    Args:
        env_name: Name of the environment (e.g., DEV, SBX)
        env_data: Dict with keys: frodo_path, platform_url, proxy (optional)
        variables: Dict of var_name -> EsvVariablePerEnv        

    Returns:
        True if all commands succeed, False if any fail.
    """

    paic_config_root = os.path.abspath(paic_config_path)
    frodo_path = env_data["frodo_path"]
    platform_url = env_data["platform_url"]
    proxy = env_data.get("proxy")

    frodo_env = os.environ.copy()
    if proxy:
        frodo_env["HTTPS_PROXY"] = proxy
        logger.info(f"Using proxy: {proxy}")

    success = True

    for var_name, var_obj in variables.items():
        var_payload = {
            "_id": var_name,
            "description": var_obj.description or "",
            "expressionType": var_obj.expressionType or "string",
            "value": var_obj.value or ""
        }

        logger.info(f"Preparing to import variable: {var_name} for env: {env_name}")

        temp_file = write_tempfile({"variable": {var_name: var_payload}}, ".variable.json")

        command = f"{frodo_path} esv variable import -i {var_name} -f {temp_file} {platform_url}"
        logger.info(f"Running import command: {command}")

        try:
            stdout, stderr = run_command(command, cwd=paic_config_root, process_env=frodo_env)
            logger.info(f"Import stdout: {stdout}")
            if stderr:
                logger.warning(f"Import stderr: {stderr}")
        except Exception as e:
            logger.error(f"Failed to import variable: {var_name} -> {str(e)}")
            success = False

        os.remove(temp_file)
        logger.info(f"Temporary file removed: {temp_file}")

    logger.info(f"Applying imported variables for env: {env_name}")
    apply_command = f"{frodo_path} esv apply -y {platform_url}"

    try:
        stdout, stderr = run_command(apply_command, cwd=paic_config_root, process_env=frodo_env)
        logger.info(f"Apply stdout: {stdout}")
        if stderr:
            logger.warning(f"Apply stderr: {stderr}")
    except Exception as e:
        logger.error(f"Failed to apply variables for env {env_name}: {str(e)}")
        success = False

    logger.info(f"Finished import_variables_for_env for {env_name} with success={success}")

    return success

def delete_variables_to_cloud(
    env_name: str,
    env_data: Dict,
    variables: Dict[str, EsvVariablePerEnv],
    paic_config_path: str = settings.PAIC_CONFIG_PATH
) -> bool:
    """
    Delete ESV variables for a specific env using frodo CLI.

    Args:
        env_name: Name of the environment (e.g., DEV, SBX)
        env_data: Dict with keys: frodo_path, platform_url, proxy (optional)
        variables: Dict of var_name -> EsvVariablePerEnv (only name is used)

    Returns:
        True if all deletes succeed, False if any fail.
    """
    paic_config_root = os.path.abspath(paic_config_path)
    frodo_path = env_data["frodo_path"]
    platform_url = env_data["platform_url"]
    proxy = env_data.get("proxy")

    frodo_env = os.environ.copy()
    if proxy:
        frodo_env["HTTPS_PROXY"] = proxy
        logger.info(f"Using proxy: {proxy}")

    success = True

    for var_name in variables.keys():
        logger.info(f"Preparing to delete variable: {var_name} for env: {env_name}")

        command = f"{frodo_path} esv variable delete -i {var_name} {platform_url}"
        logger.info(f"Running delete command: {command}")

        try:
            stdout, stderr = run_command(command, cwd=paic_config_root, process_env=frodo_env)
            logger.info(f"Delete stdout: {stdout}")
            if stderr:
                logger.warning(f"Delete stderr: {stderr}")
        except Exception as e:
            logger.error(f"Failed to delete variable: {var_name} -> {str(e)}")
            success = False

    logger.info(f"Finished delete_variables_from_cloud for {env_name} with success={success}")

    return success