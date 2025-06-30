# core/frodo/utils.py
import subprocess
import tempfile
import json
from core.logger import get_logger

logger = get_logger("__name__")

def run_command(command: str, cwd: str = ".", process_env: dict = None) -> str:
    """
    Run a shell command and return its stdout output.
    Logs stdout, stderr, and errors with your centralized logger.
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            text=True,
            capture_output=True,
            cwd=cwd,
            check=True,
            env=process_env
        )

        if result.stdout.strip():
            logger.info(f"Command output:\n{result.stdout.strip()}")
        if result.stderr.strip():
            logger.warning(f"Command stderr:\n{result.stderr.strip()}")

        return result.stdout.strip(), result.stderr.strip()

    except subprocess.CalledProcessError as e:
        logger.error(
            f"Command failed: {command} (exit code {e.returncode})",
            extra={"stderr": e.stderr.strip(), "stdout": e.stdout.strip()}
        )
        raise

def write_tempfile(data: dict, suffix: str = ".tmp") -> str:
    """
    Write dict data to a temporary file with the given suffix and return its path.
    """
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, mode="w")
    json.dump(data, temp_file)
    temp_file.close()
    return temp_file.name

def load_json(path: str):
    """Load JSON data from file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)