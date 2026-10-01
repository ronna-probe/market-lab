from data.kis import get_access_token


def main():
    result = get_access_token()

    print("KIS API 인증 요청 성공")
    print("token_type:", result.get("token_type"))
    print("expires_in:", result.get("expires_in"))


if __name__ == "__main__":
    main()
