import pandas as pd

from src.data.kis import get_access_token, get_daily_price


def main():
    # 1. KIS API 인증
    result = get_access_token()
    access_token = result["access_token"]

    # 2. 삼성전자 일봉 데이터 조회
    price_data = get_daily_price(
        access_token,
        "005930",
    )

    # 3. API 응답 중 일봉 데이터만 추출
    df = pd.DataFrame(price_data["output2"])

    # 4. 필요한 컬럼만 선택하고 이름 변경
    df = df[
        [
            "stck_bsop_date",
            "stck_oprc",
            "stck_hgpr",
            "stck_lwpr",
            "stck_clpr",
            "acml_vol",
            "acml_tr_pbmn",
        ]
    ].rename(
        columns={
            "stck_bsop_date": "date",
            "stck_oprc": "open",
            "stck_hgpr": "high",
            "stck_lwpr": "low",
            "stck_clpr": "close",
            "acml_vol": "volume",
            "acml_tr_pbmn": "trading_value",
        }
    )

    # 5. 데이터 타입 변환
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")

    numeric_columns = [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "trading_value",
    ]

    df[numeric_columns] = df[numeric_columns].apply(
        pd.to_numeric
    )

    # 6. 날짜 기준 오름차순 정렬
    df = df.sort_values("date").reset_index(drop=True)

    # 7. 결과 확인
    print("삼성전자 데이터 수집 및 정제 성공")
    print()
    print(df.head())
    print()
    print(df.dtypes)
    print()
    print("행 수:", len(df))


if __name__ == "__main__":
    main()
