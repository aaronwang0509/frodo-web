# tests/frodo/test_save_connection.py
from pathlib import Path
import json

from core.frodo.save_connection import save_connection
from core.frodo.utils import run_frodo_command

# Load once, same as in test_get_token.py
CONFIG_PATH = Path(__file__).parent.parent / "envs.json"

with open(CONFIG_PATH) as f:
    TEST_ENVS = json.load(f)

def test_save_connection():
    env = TEST_ENVS["SBX"]

    # Check if the connection already exists
    list_output = run_frodo_command(
        f"{env['frodo']} conn list"
    )

    target_url = f"{env['platformUrl'].rstrip('/')}/am"
    if target_url in list_output:
        run_frodo_command(
            f"{env['frodo']} conn delete {target_url}"
        )

    # Run save_connection() with real data
    save_connection(
        frodo_path=env["frodo"],
        platform_url=env["platformUrl"],
        service_account_id=env["serviceAccountID"],
        service_account_jwk=env["serviceAccountJWK"],
        proxy_url=env["proxy"]
    )

    output = run_frodo_command(
        f"{env['frodo']} conn list"
    )

    assert target_url in output