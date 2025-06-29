import json
import time
import base64
import os
import requests
import urllib3
from jwcrypto import jwt, jwk
from core.logger import get_logger

logger = get_logger(__name__)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def create_signed_jwt(
    service_account_id: str,
    aud: str,
    jwk_dict: dict,
    exp_seconds: int
) -> str:
    """
    Create a signed JWT for the ForgeRock Service Account.
    """
    key = jwk.JWK.from_json(json.dumps(jwk_dict))

    exp = int(time.time()) + exp_seconds
    jti = base64.urlsafe_b64encode(os.urandom(16)).decode('utf-8').rstrip('=')

    payload = {
        "iss": service_account_id,
        "sub": service_account_id,
        "aud": aud,
        "exp": exp,
        "jti": jti
    }

    token = jwt.JWT(header={"alg": "RS256"}, claims=payload)
    token.make_signed_token(key)

    logger.debug(f"Signed JWT created with jti={jti}")
    return token.serialize()

def get_service_account_access_token(
    platform_url: str,
    service_account_id: str,
    jwk_dict: dict,
    exp_seconds: int = 899,
    scope: str = "fr:am:* fr:idm:*",
    proxy_url: str | None = None
) -> str:
    """
    Request a ForgeRock PAIC Access Token using a Service Account JWK.
    """

    aud = platform_url.rstrip("/") + "/am/oauth2/access_token"
    signed_jwt = create_signed_jwt(service_account_id, aud, jwk_dict, exp_seconds)

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "client_id": "service-account",
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": signed_jwt,
        "scope": scope
    }
    proxies = {"https": proxy_url} if proxy_url else None

    logger.info(f"Requesting service account access token for SA={service_account_id} at {aud}")

    response = requests.post(aud, headers=headers, data=data, proxies=proxies, verify=False)

    if response.status_code == 200:
        token = response.json().get("access_token")
        logger.info(f"Access token retrieved successfully for SA={service_account_id}")
        return token
    else:
        logger.error(f"Failed to retrieve access token: {response.status_code} {response.text}")
        raise Exception(f"Failed to get token: {response.status_code} {response.text}")