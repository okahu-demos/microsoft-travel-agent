"""OpenAI client factory functions for the travel assistant."""

from __future__ import annotations

import os

from agent_framework.openai import OpenAIChatCompletionClient
from azure.identity.aio import AzureCliCredential
from dotenv import load_dotenv

# Load environment variables early so local .env is respected.
load_dotenv()


def create_assistants_client() -> OpenAIChatCompletionClient:
    """Create an Azure OpenAI chat completion client from environment settings."""
    deployment_name = (
        os.getenv("AZURE_OPENAI_MODEL_DEPLOYMENT_NAME")
        or os.getenv("AZURE_OPENAI_API_DEPLOYMENT")
        or os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")
    )
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-05-01-preview")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")

    if not deployment_name:
        raise RuntimeError(
            "Azure OpenAI deployment name is missing. Set AZURE_OPENAI_MODEL_DEPLOYMENT_NAME "
            "(preferred), AZURE_OPENAI_API_DEPLOYMENT, or AZURE_OPENAI_CHAT_DEPLOYMENT_NAME."
        )
    if not endpoint:
        raise RuntimeError("Azure OpenAI endpoint is missing. Set AZURE_OPENAI_ENDPOINT.")

    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    if api_key:
        return OpenAIChatCompletionClient(
            azure_endpoint=endpoint,
            model=deployment_name,
            api_version=api_version,
            api_key=api_key,
        )

    return OpenAIChatCompletionClient(
        azure_endpoint=endpoint,
        model=deployment_name,
        api_version=api_version,
        credential=AzureCliCredential(),
    )
