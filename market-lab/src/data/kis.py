import os
import requests


def get_access_token():
    app_key = os.getenv("KIS_APP_KEY")
    app_secret = os.getenv("KIS_APP_SECRET")

    url = "https://openapi.koreainvestment.com:9443/oauth2/tokenP"

    headers = {
        "content-type": "application/json"
    }

    body = {
        "grant_type": "client_credentials",
        "appkey": app_key,
        "appsecret": app_secret,
    }

    response = requests.post(
        url,
        headers=headers,
        json=body,
    )

    response.raise_for_status()

    return response.json()


if __name__ == "__main__":
    result = get_access_token()
    print(result)
