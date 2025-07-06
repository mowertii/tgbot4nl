import requests

def ask_perplexity(query: str, api_key: str, model: str = "sonar-deep-research") -> str:
    url = "https://api.perplexity.ai/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Be precise and concise."},
            {"role": "user", "content": query}
        ],
        "max_tokens": 1000,
        "temperature": 0.5
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    print("Payload:", payload)
    print("Headers:", headers)
    response = requests.post(url, json=payload, headers=headers)
    print("Response status:", response.status_code)
    print("Response text:", response.text)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]

