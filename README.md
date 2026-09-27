# DevRank

**Build. Compete. Level Up.**

DevRank is a gamified developer leaderboard application that reignites the drive to build. It tracks real GitHub contributions, ranks developers by weekly commits, and uses an AI agent to suggest personalized next projects based on each developer's experience level and tech stack.

Built for the **Authorized to Act: Auth0 for AI Agents** hackathon, DevRank uses Auth0 Token Vault to securely store and retrieve GitHub OAuth tokens on behalf of authenticated users, without ever exposing credentials to the frontend or storing raw tokens in the application database.

---

## The Problem

Many developers [beginners and intermediates alike] lose momentum. They do not know what to build next, have no visibility into their own progress, and have no community accountability keeping them active. DevRank solves this with three things:

- A **live leaderboard** ranked by weekly GitHub commits
- An **AI roadmap** that suggests 3 personalized projects based on your tech stack and activity
- A **gamified experience** that makes consistent development feel rewarding

---

## Features

- Auth0 login (Google, GitHub, or email)
- GitHub OAuth connection via Auth0 Token Vault
- Weekly contribution tracking across all owned, non-forked repositories
- Leaderboard ranked by commits in the last 7 days
- AI-powered project roadmap (OpenRouter + Mistral)
- Roadmap stored in SQLite - no repeated API calls on page load
- On-demand roadmap generation via a single button click
- GitHub token stored securely in Auth0 Token Vault, never in plain text

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Auth | Auth0 (Authlib), GitHub OAuth |
| Token Security | Auth0 Token Vault |
| Database | SQLite via Flask-SQLAlchemy |
| AI Agent | OpenRouter API (mistral-small-24b-instruct-2501 and 3.2-24b-instruct,and llama-3-8b-instruct) |
| GitHub Data | GitHub REST API v3 |
| Frontend | Jinja2, Bootstrap 5, Font Awesome |
| Caching | cachetools TTLCache |

---

## Project Structure

```
devrank/
├── app/
│   ├── __init__.py               # App factory
│   ├── config.py                 # Environment config
│   ├── extensions.py             # SQLAlchemy instance
│   ├── models.py                 # User and Roadmap DB models
│   ├── oauth.py                  # Auth0 and GitHub OAuth registration
│   ├── routes.py                 # All Flask routes
│   ├── services/
│   │   ├── ai_service.py         # OpenRouter AI project suggestions
│   │   ├── github_service.py     # GitHub API integration
│   │   ├── leaderboard_service.py# Leaderboard aggregation
│   │   └── token_vault_service.py# Auth0 Token Vault integration
│   ├── static/
│   │   └── index.css             # Global styles
│   └── templates/
│       ├── base.html             # Base layout with navbar
│       ├── index.html            # Landing page
│       ├── dashboard.html        # User dashboard with AI roadmap
│       ├── leaderboard.html      # Weekly leaderboard
│       └── profile.html          # User profile and GitHub connect
├── .env                          # Environment variables (not committed)
├── requirements.txt
└── run.py
```

---

## Prerequisites

- Python 3.10+
- An [Auth0 account](https://auth0.com/signup)
- A [GitHub OAuth App](https://github.com/settings/developers)
- An [OpenRouter account](https://openrouter.ai) with at least $5 credit

---

## Auth0 Setup

You need to create two applications and configure one social connection in your Auth0 tenant.

### 1. Regular Web Application

```
Auth0 Dashboard
-> Applications -> Applications -> Create Application
-> Name: DevRank
-> Type: Regular Web Application
-> Create
```

**Settings tab:**
```
Allowed Callback URLs: http://127.0.0.1:5000/callback
Allowed Logout URLs: http://127.0.0.1:5000
Allowed Web Origins: http://127.0.0.1:5000
-> Save Changes
```

**Advanced Settings -> Grant Types:**
```
Check: Authorization Code
Check: Refresh Token
Check: Token Vault
-> Save Changes
```

Note down: `Domain`, `Client ID`, `Client Secret` to be save in the .env file

---

### 2. GitHub Social Connection

```
Auth0 Dashboard
-> Authentication -> Social -> Create Connection -> GitHub
-> paste your GitHub OAuth App Client ID and Client Secret
-> Permissions: check read:user and repo
-> Purpose: Authentication and Connected Accounts for Token Vault
-> Create
```

**Applications tab of the GitHub connection:**
```
-> enable toggle for DevRank app
-> Save
```

---

### 3. Machine to Machine Application (Token Exchange)

```
Auth0 Dashboard
-> Applications -> Applications -> Create Application
-> Name: DevRank Token Exchange
-> Type: Machine to Machine
-> Create
```

When prompted to authorize an API:
```
-> Select: Auth0 Management API
-> Permissions: select these four only:
   read:users
   update:users
   read:users_app_metadata
   update:users_app_metadata
-> Authorize
```

**Advanced Settings -> Grant Types:**
```
Check: Client Credentials
-> Save Changes
```

Note down: `Client ID`, `Client Secret` once again.

---

### 4. Verify from the API side

```
Applications -> APIs -> Auth0 Management API
-> Application Access tab
-> DevRank Token Exchange must show AUTHORIZED for Client Access
```

---

## GitHub OAuth App Setup

```
GitHub -> Settings -> Developer Settings -> OAuth Apps -> New OAuth App

Application name: DevRank
Homepage URL: http://127.0.0.1:5000
Authorization callback URL: http://127.0.0.1:5000/github/callback
-> Register application
```

Note down: `Client ID`, `Client Secret`

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/katGhost/devrank.git
cd devrank
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create your `.env` file

Create a `.env` file in the project root:

```bash
# Flask
SECRET_KEY=your-fixed-secret-key-here

# Auth0 - Regular Web Application
AUTH0_CLIENT_ID=your-devrank-app-client-id
AUTH0_CLIENT_SECRET=your-devrank-app-client-secret
AUTH0_DOMAIN=your-tenant.eu.auth0.com
AUTH0_REDIRECT_URI=http://127.0.0.1:5000/callback

# Auth0 - Machine to Machine (Token Exchange)
AUTH0_CUSTOM_API_CLIENT_ID=your-m2m-client-id
AUTH0_CUSTOM_API_CLIENT_SECRET=your-m2m-client-secret
AUTH0_AUDIENCE=https://your-tenant.eu.auth0.com/api/v2/

# GitHub OAuth App
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

# GitHub connection name in Auth0 (default: github)
GITHUB_CONNECTION_NAME=github

# OpenRouter
OPENROUTER_API_KEY=sk-or-your-key-here
```

### 5. Run the application

```bash
flask run
```

Navigate to `http://127.0.0.1:5000`

---

## How It Works

### Authentication Flow

```
User clicks Login
      |
      v
Auth0 handles identity (Google, email, or GitHub login)
      |
      v
User session created -> stored in SQLite by Auth0 user ID
      |
      v
User clicks Connect GitHub (on Profile page)
      |
      v
GitHub OAuth -> token stored in Auth0 Token Vault
      |
      v
GitHub username stored in DB for display purposes only
```

### Token Vault Flow

```
GitHub OAuth completes -> access token returned
      |
      v
connect_github_account() called
      |
      v
M2M client exchanges credentials for Management API token
      |
      v
GitHub token linked to Auth0 user identity via /api/v2/users/{id}/identities
      |
      v
Token stored securely in Auth0 Token Vault
      |
      v
On dashboard load: get_github_token_from_vault() retrieves it
      |
      v
Falls back to DB token if vault retrieval fails
```

### AI Roadmap Flow

```
User clicks Request Roadmap
      |
      v
GitHub token retrieved from Token Vault
      |
      v
summarize_user_activity() fetches repos and commits
      |
      v
Experience level classified: Beginner / Intermediate / Advanced
      |
      v
generate_next_projects() sends profile to OpenRouter (Mistral)
      |
      v
3 project suggestions returned as JSON
      |
      v
Saved to Roadmap table in SQLite -> replaces old suggestions
      |
      v
Dashboard renders from DB -> no API call on subsequent loads
```

---

## Key Files Explained

### `app/services/token_vault_service.py`

Handles all Auth0 Token Vault operations:

- `get_management_api_token()` — exchanges M2M client credentials for a Management API bearer token
- `connect_github_account()` — links a GitHub identity to an Auth0 user profile, storing the token in the vault
- `get_github_token_from_vault()` — retrieves the stored GitHub access token for a given Auth0 user ID

### `app/services/github_service.py`

Wraps the GitHub REST API:

- `get_user_repos()` — paginates through all owned, non-forked repositories
- `get_repo_commits()` — fetches commits by the authenticated user since a given date
- `get_weekly_contributions()` — aggregates commits across all repos in the last 7 days, with 1-hour TTL cache
- `summarize_user_activity()` — builds a developer profile used by the AI agent

### `app/services/ai_service.py`

Calls OpenRouter with a model fallback chain:

```python
MODELS = [
    "mistralai/mistral-small-24b-instruct-2501",
    "mistralai/mistral-small-3.2-24b-instruct",
    "meta-llama/llama-3-8b-instruct"
]
```

Prompts the model for exactly 3 project suggestions in strict JSON format. Strips markdown fences, validates structure, and falls back gracefully on failure.

### `app/models.py`

Two models:

```python
class User:
    auth0_id      # unique Auth0 sub (e.g. google-oauth2|123)
    name, email, picture, nickname
    github_username     # stored for display and sanity checks
    github_token    # fallback only, Token Vault is primary

class Roadmap:
    user_id     # foreign key to User
    title
    description
    learning_outcome
    created_at
```

---

## Requirements

```
flask
flask-sqlalchemy
authlib
requests
python-dotenv
cachetools
werkzeug
```

Full list in `requirements.txt`.

---

## Environment Variables Reference

| Variable | Description |
|---|---|
| `SECRET_KEY` | Flask session secret — must be fixed string, not random |
| `AUTH0_CLIENT_ID` | DevRank Regular Web App client ID |
| `AUTH0_CLIENT_SECRET` | DevRank Regular Web App client secret |
| `AUTH0_DOMAIN` | Your Auth0 tenant domain |
| `AUTH0_REDIRECT_URI` | Must match Auth0 allowed callback URLs |
| `AUTH0_CUSTOM_API_CLIENT_ID` | M2M Token Exchange app client ID |
| `AUTH0_CUSTOM_API_CLIENT_SECRET` | M2M Token Exchange app client secret |
| `AUTH0_AUDIENCE` | Management API audience URL |
| `GITHUB_CLIENT_ID` | GitHub OAuth App client ID |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth App client secret |
| `GITHUB_CONNECTION_NAME` | Social connection name in Auth0 (default: github) |
| `OPENROUTER_API_KEY` | OpenRouter API key |

---

## Security Notes

- GitHub tokens are stored in Auth0 Token Vault, not in the application database
- The application database only stores the GitHub username for display purposes
- Session cookies are HTTP-only and SameSite=Lax
- `OAUTHLIB_INSECURE_TRANSPORT=1` is set for local development only — remove for production
- `SESSION_COOKIE_SECURE` must be set to `True` in production with HTTPS

---

## Known Limitations

- Leaderboard only includes users who have signed up and connected GitHub
- AI suggestions require GitHub to be connected
- OpenRouter free tier models are rate-limited - a minimum $5 credit is recommended
- Token Vault requires a confidential client (Regular Web Application), not a Single Page Application

---

## Bonus Blog Post

Building DevRank taught me more about OAuth in one weekend than months of reading docs ever could.

I came into this hackathon knowing almost nothing about OAuth flows and even less about AI agents. The concept sounded straightforward — connect Auth0, connect GitHub, show some data. What I did not expect was how much the identity layer would dominate the development time.

The first wall I hit was the callback URL mismatch. Auth0 kept rejecting my redirect URI, and after hours of debugging I realized the problem was not the URL itself — it was that I had hardcoded `redirect_uri` in `oauth.register()`, which competed with the dynamically generated one from `url_for()`. Removing it fixed everything.

The second wall was Token Vault. The concept is elegant: instead of storing GitHub tokens in my database, Auth0 stores them securely and my app exchanges its own access token for a fresh GitHub token at runtime. In practice, getting there required creating two separate Auth0 applications — a Regular Web App for user login and a Machine to Machine app for the token exchange — and correctly configuring Management API permissions on both. The 403 errors I hit along the way were caused by being on two different Auth0 tenants simultaneously without realizing it.

The AI agent piece was surprisingly the smoothest part once the auth layer was solid. The key insight was decoupling AI calls from page loads entirely. Instead of calling OpenRouter on every dashboard visit, I store the suggestions in SQLite and only regenerate them when the user explicitly clicks a button. This made the app faster, cheaper to run, and more consistent.

What I am most proud of is the fallback architecture throughout — Token Vault fails gracefully to the DB, AI models fail through a chain of alternatives, and GitHub errors never crash the leaderboard. For a beginner project, that defensive thinking felt like a genuine step forward.