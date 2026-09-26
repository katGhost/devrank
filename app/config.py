import os
from dotenv import load_dotenv


load_dotenv(override=True)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# print(os.environ.get("DATABASE_URL"))

class Config:
    # App
    SECRET_KEY = os.getenv("SECRET_KEY")

    # Auth0
    AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
    AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET")
    AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
    AUTH0_REDIRECT_URI = os.getenv("AUTH0_REDIRECT_URI")

    # GitHub
    GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
    GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
    GITHUB_API_BASE_URL = "https://api.github.com"
    GITHUB_AUTHORIZATION_URL = os.getenv('GITHUB_AUTHORIZATION_URL')

    # Token vault configuration
    AUTH0_CUSTOM_API_CLIENT_ID = os.getenv("AUTH0_CUSTOM_API_CLIENT_ID")
    AUTH0_CUSTOM_API_CLIENT_SECRET = os.getenv("AUTH0_CUSTOM_API_CLIENT_SECRET")
    GITHUB_CONNECTION_NAME = os.getenv("GITHUB_CONNECTION_NAME", "github")

    # Postgres stored in project root
    # SQLALCHEMY_DATABASE_URI = "sqlite:///devleaderboard.db"
    DATABASE_URL = os.environ.get("DATABASE_URL")
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("SQLALCHEMY_DATABASE_URI") or DATABASE_URL
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")