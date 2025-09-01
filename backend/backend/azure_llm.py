import os
from openai import AzureOpenAI

def get_azure_openai_client():
    """Returns an AzureOpenAI client configured via environment variables."""
    return AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )

def generate_response(client: AzureOpenAI, prompt: str) -> str:
    """Generates a response from the Azure OpenAI LLM."""
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    system_prompt = os.getenv("LLM_SYSTEM_AR", "You are a helpful assistant.")

    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        max_tokens=150,
        temperature=0.7,
    )
    return response.choices[0].message.content