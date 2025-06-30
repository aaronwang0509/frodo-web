import os

from core.logger import get_logger
from core.frodo.utils import run_command, write_tempfile

logger = get_logger("__name__")

def save_connection(
    frodo_path: str,
    platform_url: str,
    service_account_id: str,
    service_account_jwk: dict,
    proxy_url: str = None
) -> None:
    """
    Save the Frodo connection config for the given environment using a service account.
    """

    # Write temp JWK file
    jwk_temp_file = write_tempfile(service_account_jwk, suffix=".jwk")
    logger.debug(f"Temporary JWK file created: {jwk_temp_file}")

    # Build the Frodo command
    command = (
        f"{frodo_path} conn save "
        f"--sa-id {service_account_id} "
        f"--sa-jwk-file {jwk_temp_file} "
        f"{platform_url.rstrip('/')}/am"
    )

    # Prepare process environment
    frodo_env = os.environ.copy()
    if proxy_url:
        frodo_env["HTTPS_PROXY"] = proxy_url
        logger.info(f"Using proxy: {proxy_url}")

    logger.info(f"Running Frodo save connection: {command}")

    # Run the Frodo command
    run_command(command, process_env=frodo_env)

    logger.info("Frodo connection configuration saved successfully.")

    # Clean up temp file
    try:
        os.remove(jwk_temp_file)
        logger.debug(f"Temporary JWK file removed: {jwk_temp_file}")
    except Exception as e:
        logger.warning(f"Failed to delete temp JWK file: {jwk_temp_file} - {str(e)}")