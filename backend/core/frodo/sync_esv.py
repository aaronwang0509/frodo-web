# core/frodo/sync_esv.py
import os

from core.logger import get_logger
from core.frodo.utils import load_json

logger = get_logger("__name__")

def pull_variables_from_local(paic_config_path: str, env_name: str) -> dict:
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
                variables[var_name] = {
                    "description": var_content.get("description", ""),
                    "expressionType": var_content.get("expressionType", "string"),
                    "value": var_content.get("value", "")
                }

    logger.info(f"Total variables collected: {len(variables)}")
    return variables