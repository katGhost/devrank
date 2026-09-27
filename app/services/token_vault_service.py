import requests
import os
from dotenv import load_dotenv
from urllib.parse import quote

load_dotenv(override=True)

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_CUSTOM_API_CLIENT_ID = os.getenv("AUTH0_CUSTOM_API_CLIENT_ID")
AUTH0_CUSTOM_API_CLIENT_SECRET = os.getenv("AUTH0_CUSTOM_API_CLIENT_SECRET")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE")
GITHUB_CONNECTION_NAME = os.getenv("GITHUB_CONNECTION_NAME", "github")


def get_management_api_token():
    response = requests.post(
        f"https://{AUTH0_DOMAIN}/oauth/token",
        json={
            "grant_type": "client_credentials",
            "client_id": AUTH0_CUSTOM_API_CLIENT_ID,
            "client_secret": AUTH0_CUSTOM_API_CLIENT_SECRET,
            "audience": AUTH0_AUDIENCE,
        }
    )
    response.raise_for_status()
    return response.json()["access_token"]


def get_github_token_from_vault(auth0_user_id):
    try:
        mgmt_token = get_management_api_token()

        # encode the user_id to handle special characters like |
        encoded_user_id = quote(auth0_user_id, safe='')

        response = requests.get(
            f"https://{AUTH0_DOMAIN}/api/v2/users/{encoded_user_id}",
            headers={
                "Authorization": f"Bearer {mgmt_token}",
                "Content-Type": "application/json",
            }
        )
        response.raise_for_status()
        user_data = response.json()

        identities = user_data.get("identities", [])
        for identity in identities:
            if identity.get("connection") == GITHUB_CONNECTION_NAME:
                access_token = identity.get("access_token")
                if access_token:
                    return access_token

        return None

    except Exception as e:
        print(f'Token vault error: {e}')
        return None


def connect_github_account(auth0_user_id, github_access_token):
    try:
        mgmt_token = get_management_api_token()

        # encode the user_id to handle special characters like |
        encoded_user_id = quote(auth0_user_id, safe='')

        response = requests.post(
            f"https://{AUTH0_DOMAIN}/api/v2/users/{encoded_user_id}/identities",
            headers={
                "Authorization": f"Bearer {mgmt_token}",
                "Content-Type": "application/json",
            },
            json={
                "provider": "github",
                "connection": GITHUB_CONNECTION_NAME,
                "access_token": github_access_token,
            }
        )
        print("VAULT LINK RESPONSE:", response.status_code, response.json())
        response.raise_for_status()
        return True

    except Exception as e:
        Print(f'Linking error {e}')
        return False