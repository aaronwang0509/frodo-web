# tests/frodo/test_sync_esv.py
import json
from pathlib import Path

from core.frodo.sync_esv import pull_variables_from_local
from tests.settings import settings

# Load envs.json
CONFIG_PATH = Path(__file__).parent.parent / "envs.json"

with open(CONFIG_PATH) as f:
    TEST_ENVS = json.load(f)

def test_sync_esv_pull():
    env = TEST_ENVS["SBX"]

    result = pull_variables_from_local(
        paic_config_path=settings.PAIC_CONFIG_PATH,
        env_name="SBX",
    )

    print("=== SYNC ESV PULL RESULT ===")
    print(json.dumps(result, indent=2))