# tests/frodo/test_update_and_push.py
import json
from pathlib import Path

from core.frodo.update_and_push import update_and_push
from tests.settings import settings

# Load envs.json
CONFIG_PATH = Path(__file__).parent.parent / "envs.json"

with open(CONFIG_PATH) as f:
    TEST_ENVS = json.load(f)

def test_update_and_push():
    env = TEST_ENVS["SBX"]

    update_and_push(
        paic_config_path=settings.PAIC_CONFIG_PATH,
        branch_name=settings.PAIC_CONFIG_BRANCH_NAME,
        frodo_path=env["frodo"],
        host_url=env["platformUrl"],
        env_name="SBX",
        proxy_url=env["proxy"],
        git_user_name="Aaron Wang",
        git_user_email="qiushiwang0702@gmail.com"
    )
