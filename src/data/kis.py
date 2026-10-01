import os
import requests
from datetime import datetime, timedelta  # backfill


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


def get_daily_price(
    access_token,
    stock_code,
    start_date,
    end_date,
):
    url = "https://openapi.koreainvestment.com:9443/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"

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
    result = get_access_token()
    print(result)


def get_daily_price_range(
    access_token,
    stock_code,
    start_date,
    end_date,
):
    start = datetime.strptime(
        start_date,
        "%Y%m%d",
    ).date()

    end = datetime.strptime(
        end_date,
        "%Y%m%d",
    ).date()

    all_rows = []

    chunk_start = start

    while chunk_start <= end:
        chunk_end = min(
            chunk_start + timedelta(days=90),
            end,
        )

        chunk_start_str = chunk_start.strftime("%Y%m%d")
        chunk_end_str = chunk_end.strftime("%Y%m%d")

        print(
            "API 조회:",
            stock_code,
            chunk_start_str,
            "~",
            chunk_end_str,
        )

        result = get_daily_price(
            access_token,
            stock_code,
            chunk_start_str,
            chunk_end_str,
        )

        rows = result.get("output2", [])

        print(
            "  반환 행 수:",
            len(rows),
        )

        all_rows.extend(rows)

        chunk_start = chunk_end + timedelta(days=1)

    return all_rows
