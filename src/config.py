"""
Loads configuration/secrets from environment variables.

"""

import os
from dotenv import load_dotenv

load_dotenv()

def get_secret(key: str) -> str:
    """
    Get a secret value, checking Streamlit's secrets store first
    (for cloud deployment), falling back to environment variables /
    .env (for local development).

    Args:
        key (str): Secret name, e.g. "ANTHROPIC_API_KEY".

    Returns:
        str: The secret value.

    Raises:
        EnvironmentError: If the key isn't found in either location.
    """
    try:
        import streamlit as st
        if key in st.secrets:
            return st.secrets[key]
    except (ImportError, FileNotFoundError):
        pass

    value = os.environ.get(key)
    if value:
        return value

    raise EnvironmentError(f"{key} not found in Streamlit secrets or environment")


ANTHROPIC_API_KEY = get_secret("ANTHROPIC_API_KEY")
GITHUB_TOKEN = get_secret("GITHUB_TOKEN")