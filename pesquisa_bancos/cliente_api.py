import requests

API_URL = "https://brasilapi.com.br/api/banks/v1"

def fetch_banks():  # <- Verifique se o nome está exatamente assim, sem espaços antes do def
    """Consome a API pública do Brasil API e retorna uma lista de dicionários."""
    try:
        response = requests.get(API_URL, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return []