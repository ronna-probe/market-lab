from src.data.kis import get_access_token, get_daily_price


def main():
    result = get_access_token()

    print("KIS API 인증 요청 성공")
    print("token_type:", result.get("token_type"))
    print("expires_in:", result.get("expires_in"))

    price_data = get_daily_price(
        result["access_token"],
        "005930",
    )

    print("삼성전자 시세 조회 성공")
    print(price_data)


if __name__ == "__main__":
    main()
