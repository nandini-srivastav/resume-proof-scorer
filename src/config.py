"""
Loads configuration/secrets from environment variables.
Boilerplate only — nothing to implement here beyond adding new
config values as the project grows.
"""

import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if not ANTHROPIC_API_KEY:
    raise EnvironmentError("Missing ANTHROPIC_API_KEY — copy .env.example to .env and fill it in.")
