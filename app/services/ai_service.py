import requests
import json
import re
from app.config import Config

OPENROUTER_API_KEY = Config.OPENROUTER_API_KEY

MODELS = [
    "mistralai/mistral-small-24b-instruct-2501",
    "mistralai/mistral-small-3.2-24b-instruct",
    "meta-llama/llama-3-8b-instruct"
]

def clean_json(content: str):
    """Remove markdown/code fences and trim."""
    content = re.sub(r"```json|```", "", content).strip()
    return content


def generate_next_projects(user_activity_summary):
    prompt = """
You are an expert senior software engineer and developer mentor.

Your task is to analyze a developer profile and generate personalized project recommendations.

Return ONLY valid JSON (no markdown, no explanation).

JSON Schema:
{
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "description": {"type": "string"},
            "learning_outcome": {"type": "string"}
        },
        "required": ["title", "description", "learning_outcome"]
    }
}
"""

    for model in MODELS:
        prompt += f"""

<Developer Profile>
- Experience Level: {user_activity_summary.get('experience_level', 'unknown')}
- Languages: {', '.join(user_activity_summary.get('languages_used', []))}
- Weekly Activity: {user_activity_summary.get('commits_last_week', 0)}
</Developer Profile>
"""

    for model in MODELS:
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 500,
                    "temperature": 0.7
                },
                timeout=15
            )

            data = response.json()

            # Skip failed responses
            if response.status_code != 200 or "error" in data:
                print(f"Model failed: {model}", data)
                continue

            print(f"Using model: {model}")  # see if it models are reached

            # Extract content safely
            content = data["choices"][0]["message"]["content"]

            # clean markdown
            content = clean_json(content)

            # parse JSON
            parsed = json.loads(content)

            # validate structure
            if isinstance(parsed, list) and len(parsed) >= 2:
                return parsed[:3]

            print(f"Invalid structure from {model}: {parsed}")

        except Exception as e:
            print(f"Exception with {model}: {e}")
            continue

    #  safe fallback -> prevents UI crash
    return [
        {
            "title": "AI Suggestion Unavailable",
            "description": "We couldn't generate personalized projects right now.",
            "learning_outcome": "Try again later"
        }
    ]


# completion=client.chat.completions.create(
#     model="gpt-3.5-turbo",
#     messages=[
#         {
#             "role": "system",
#             "content": "You are an expert florist helpdesk assistant"
#         },
#         {
#             "role": "user",
#             "content": "Are Lilys the best flowers for a wedding?"
#         }
#     ]
# )

# res = completion.choices[0].message.content
# print(res)

# def suggest_projects(user):
#     suggestions = {
#         "Python": [
#             "Build a Flask REST API",
#             "Contribute to a Python open-source repo",
#             "Create a CLI tool"
#         ],
#         "JavaScript": [
#             "Build a React app",
#             "Contribute to a JS repo",
#             "Create a browser extension"
#         ]
#     }

#     return suggestions.get(user, ["Explore open source projects"])

"""try:
    MODELS = [
        "mistralai/mistral-small-24b-instruct-2501",  # primary
        "mistralai/mistral-small-3.2-24b-instruct",  # fallback
        "meta-llama/llama-3-8b-instruct"             # backup
    ]

    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            # free and actively available on OpenRouter -> have to pay $5
            # free not available -> no endpoints reached
            "model": f"{for model in MODELS}",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 500,
            "temperature": 0.7,
            "response_format": {"type": "json_object"}
        }
    )

    data = response.json()
    # proper openrouter error handling
    if "error" in data:
        raise Exception(data["error"])
    print('MODEL RAW RESPONSE:', json.dumps(data, indent=2))
    content = data["choices"][0]["message"]["content"].strip()

    # strip markdown code fences if model wraps response in them
    content = re.sub(r"```json|```", "", content).strip()

    suggestions = json.loads(content)

    # guard against model returning something other than a list
    if not isinstance(suggestions, list):
        raise ValueError("Response is not a list")

    return suggestions

except Exception as e:
    print(f"AI generation error: {e}")
    # always return a list so the template loop does not break
    return [
        {
            "title": "Could not load suggestions",
            "description": "There was an issue generating your roadmap. Try again later.",
            "learning_outcome": ""
        }
    ]"""