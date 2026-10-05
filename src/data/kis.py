import os

import requests


KIS_BASE_URL = "https://openapi.koreainvestment.com:9443"


def get_access_token():
    """KIS API Access Token을 발급받는다."""
    app_key = os.getenv("KIS_APP_KEY")
    app_secret = os.getenv("KIS_APP_SECRET")

    url = f"{KIS_BASE_URL}/oauth2/tokenP"

    headers = {
        "content-type": "application/json",
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


def get_daily_price(
    access_token,
    stock_code,
    start_date,
    end_date,
):
    """KIS API에서 종목의 일봉 데이터를 조회한다."""
    url = (
        f"{KIS_BASE_URL}"
        "/uapi/domestic-stock/v1/quotations/"
        "inquire-daily-itemchartprice"
    )

    headers = {
        "content-type": "application/json",
        "authorization": f"Bearer {access_token}",
        "appkey": os.getenv("KIS_APP_KEY"),
        "appsecret": os.getenv("KIS_APP_SECRET"),
        "tr_id": "FHKST03010100",
    }

    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": stock_code,
        "FID_INPUT_DATE_1": start_date,
        "FID_INPUT_DATE_2": end_date,
        "FID_PERIOD_DIV_CODE": "D",
        "FID_ORG_ADJ_PRC": "1",
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
    )

    response.raise_for_status()

    return response.json()