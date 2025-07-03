# core/frodo/update_and_push.py
import os
import datetime
import shutil

from core.logger import get_logger
from core.settings import settings
from core.frodo.utils import run_command

logger = get_logger("__name__")

def clean_old_configs(configs_dir: str):
    logger.info(f"Cleaning old config folders in: {configs_dir}")
    if not os.path.exists(configs_dir):
        return
    for entry in os.listdir(configs_dir):
        entry_path = os.path.join(configs_dir, entry)
        if os.path.isdir(entry_path):
            shutil.rmtree(entry_path)
            logger.info(f"Deleted: {entry_path}")

def update_and_push(
    env_name: str,
    frodo_path: str,
    platform_url: str,
    proxy: str | None,
    git_user_name: str,
    git_user_email: str,
    paic_config_path: str = settings.PAIC_CONFIG_PATH,
    branch_name: str = settings.PAIC_CONFIG_BRANCH_NAME,
) -> dict:
    """
    Run Frodo config export for the given environment,
    then commit & push changes to the specified branch if needed.
    Returns a dict describing the success/failure of each step.
    """

    result = {
        "env_name": env_name,
        "branch_name": branch_name,
        "frodo_export_status": "pending",
        "git_push_status": "pending",
        "stdout": "",
        "stderr": "",
        "overall_status": "pending"
    }

    paic_config_root = os.path.abspath(paic_config_path)
    configs_dir = os.path.join(paic_config_root, "configs", env_name)

    logger.info(f"Starting update_and_push for environment '{env_name}' on branch '{branch_name}'")

    try:
        # Set Git user name and email for this push
        run_command(f'git config user.name "{git_user_name}"', cwd=paic_config_root)
        run_command(f'git config user.email "{git_user_email}"', cwd=paic_config_root)

        # Make sure we are on the correct branch and up to date
        run_command(f"git checkout {branch_name}", cwd=paic_config_root)
        run_command(f"git pull origin {branch_name}", cwd=paic_config_root)
    except Exception as e:
        result["overall_status"] = "failed"
        result["stderr"] = str(e)
        logger.error(f"Git setup failed: {e}")
        return result

    try:
        # Clean old configs for the environment
        clean_old_configs(configs_dir)
    except Exception as e:
        result["overall_status"] = "failed"
        result["stderr"] = str(e)
        logger.error(f"Cleaning old configs failed: {e}")
        return result

    # Build Frodo command environment
    frodo_env = os.environ.copy()
    if proxy:
        frodo_env["HTTPS_PROXY"] = proxy
        logger.info(f"Using proxy: {proxy}")

    # Run Frodo config export
    logger.info("Running Frodo config export...")
    try:
        export_stdout, export_stderr = run_command(
            f"{frodo_path} config export -sxoAND {configs_dir} {platform_url}",
            cwd=paic_config_root,
            process_env=frodo_env
        )
        result["frodo_export_status"] = "success"
        result["stdout"] = export_stdout
        result["stderr"] = export_stderr
    except Exception as e:
        result["frodo_export_status"] = "failed"
        result["stderr"] = str(e)
        logger.error(f"Frodo export failed: {e}")
        result["overall_status"] = "failed"
        return result

    # Check for changes
    try:
        status_stdout, status_stderr = run_command(f"git status --porcelain configs/{env_name}", cwd=paic_config_root)
    except Exception as e:
        result["git_push_status"] = "failed"
        result["stderr"] = str(e)
        logger.error(f"Git status check failed: {e}")
        result["overall_status"] = "failed"
        return result

    if status_stdout.strip():
        logger.info("Changes detected, committing to Git...")
        try:
            run_command(f"git add configs/{env_name}", cwd=paic_config_root)
            commit_msg = f"Automated update for {env_name} on {datetime.datetime.now(datetime.UTC).isoformat()}"
            run_command(f'git commit -m "{commit_msg}"', cwd=paic_config_root)
            run_command(f"git push origin {branch_name}", cwd=paic_config_root)
            logger.info("Changes pushed successfully.")
            result["git_push_status"] = "success"
            result["stdout"] = status_stdout
        except Exception as e:
            logger.error(f"Git commit/push failed: {e}")
            result["git_push_status"] = "failed"
            result["stderr"] = str(e)
            result["overall_status"] = "failed"
            return result
    else:
        logger.info("No changes detected, skipping commit.")
        result["git_push_status"] = "no_changes"

    result["overall_status"] = "success"
    logger.info(f"update_and_push completed for '{env_name}' on branch '{branch_name}'")

    return result