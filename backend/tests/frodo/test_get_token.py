# tests/frodo/test_get_token.py
import json
import os
from pathlib import Path

import pytest

from core.frodo.get_token import get_service_account_access_token

# Load your test config once
CONFIG_PATH = Path(__file__).parent.parent / "envs.json"

with open(CONFIG_PATH) as f:
    TEST_ENVS = json.load(f)

@pytest.mark.skipif(
    not TEST_ENVS.get("SBX"),
    reason="SBX environment not configured"
)
def test_get_service_account_access_token():
    env = TEST_ENVS["SBX"]

    token = get_service_account_access_token(
        platform_url=env["platformUrl"],
        service_account_id=env["serviceAccountID"],
        jwk_dict=env["serviceAccountJWK"],
        exp_seconds=env.get("expSeconds", 899),
        scope=env.get("scope", "fr:am:* fr:idm:*"),
        proxy_url=env.get("proxy") or None
    )

    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 20  # simple sanity check