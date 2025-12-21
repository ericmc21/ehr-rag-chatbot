"""
Epic FHIR OAuth Client
Handles authentication using private key JWT (Backend Services) for Epic FHIR API.
"""

import os
import time
import jwt
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class EpicAuthClient:
    """
    Handles Epic FHIR authentication using client credentials flow with JWT
    """

    def __init__(self):
        self.client_id = os.getenv("EPIC_CLIENT_ID")
        self.token_url = os.getenv("EPIC_TOKEN_URL")
        self.private_key_path = os.getenv("EPIC_PRIVATE_KEY_PATH")
        self.key_id = os.getenv("EPIC_KEY_ID")

        # Validate configuration
        if not all(
            [self.client_id, self.token_url, self.private_key_path, self.key_id]
        ):
            raise ValueError(
                "Missing required Epic configuration. Check your .env file."
            )

        # Load private key
        self.private_key = self._load_private_key()

        # Token caching
        self.access_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None

    def _load_private_key(self) -> str:
        """
        Load private key from file

        :param self: Description
        :return: Description
        :rtype: str
        """
        key_path = Path(self.private_key_path)
        if not key_path.exists():
            raise FileNotFoundError(
                (f"Private key not found at {self.private_key_path}")
            )

        with open(key_path, "r") as f:
            return f.read()

    def _create_jwt_assertion(self) -> str:
        """
        Create JWT assertion for Epic authentication
        Epic requires a signed JWT with specific claims.

        :param self: Description
        :return: Description
        :rtype: str
        """
        now = int(time.time())

        # JWT payload (claims)
        payload = {
            "iss": self.client_id,  # Issuer: your client ID
            "sub": self.client_id,  # Subject: also your client ID
            "aud": self.token_url,  # Audience: token endpoint
            "jti": f"{self.client_id}--{now}",  # Unique identifier for the JWT
            "exp": now + 300,  # Expiration time (5 minutes from now)
            "iat": now,  # Issued at time
        }

        # JWT headers
        headers = {
            "kid": self.key_id,  # Key ID
            "alg": "RS384",  # Algorithm (Epic supports RS384)
            "typ": "JWT",
        }

        # Sign the JWT with private key
        token = jwt.encode(
            payload,
            self.private_key,
            algorithm="RS384",
            headers=headers,
        )

        return token

    def get_access_token(self, force_refresh: bool = False) -> str:
        """
        Get access token, using cached token if still valid.

        :param self: Description
        :param force_refresh: Force getting a new token even if cached one is valid
        :type force_refresh: bool
        :return: Access token string
        :rtype: str
        """
        if not force_refresh and self.access_token and self.token_expiry:
            if datetime.now() < self.token_expiry - timedelta(minutes=5):
                print("Using cached access token")
                return self.access_token
        print("Requesting new access token from Epic...")

        # Create JWT assertion
        jwt_assertion = self._create_jwt_assertion()

        # Request access token
        data = {
            "grant_type": "client_credentials",
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            "client_assertion": jwt_assertion,
        }

        try:
            response = requests.post(
                self.token_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()

            token_data = response.json()

            # Cache the token
            self.access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)  # Default to 1 hour
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in)

            print(f"Access token obtained (expires in {expires_in}s)")
            return self.access_token

        except requests.exceptions.RequestException as e:
            print(f"x Authetication failed: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"Response: {e.response}")
            raise


def test_authentication():
    """
    Test Epic authentication
    """
    print("=" * 60)
    print("Testing Epic FHIR Authentication")
    print("=" * 60)

    try:
        client = EpicAuthClient()
        token = client.get_access_token()
        print(f"\n Successfully authenticated!")
        print(f"Token preview: {token[:50]}")

    except Exception as e:
        print(f"\n x authentication failed: {e}")
        raise


if __name__ == "__main__":
    test_authentication()
