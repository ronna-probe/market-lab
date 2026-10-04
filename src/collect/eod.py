from datetime import datetime

import pandas as pd

from src.data.kis import (
    get_access_token,
    get_daily_price_range,
)
from src.data.universe import get_kospi_tickers


def run_eod_collection(
    batch_start=0,
    batch_size=50,
):
    """
    EOD 시장 데이터를 수집한다.

    실행일 당일의 데이터를 수집한다.
    """

    # --------------------------------------------------
    # 1. 수집 기준일
    # --------------------------------------------------

    collection_date = datetime.now().strftime("%Y%m%d")

    print()
    print("EOD 수집 기준일:", collection_date)

    # --------------------------------------------------
    # 2. KIS Access Token
    # --------------------------------------------------

    access_token = get_access_token()

    print()
    print("KIS Access Token 발급 성공")

    # --------------------------------------------------
    # 3. KOSPI Universe
    # --------------------------------------------------

    tickers = get_kospi_tickers()

    print()
    print("KOSPI 종목 Universe 생성 성공")
    print("전체 종목 수:", len(tickers))
    print("앞 10개:", tickers[:10])

    # --------------------------------------------------
    # 4. Batch
    # --------------------------------------------------

    batch_tickers = tickers[
        batch_start:batch_start + batch_size
    ]

    print()
    print("수집 대상 종목 수:", len(batch_tickers))
    print(
        "Batch 범위:",
        batch_start,
        "~",
        batch_start + len(batch_tickers) - 1,
    )

    # --------------------------------------------------
    # 5. 종목별 EOD 데이터 수집
    # --------------------------------------------------

    all_data = []

    for ticker in batch_tickers:

        print()
        print("데이터 수집:", ticker)

        rows = get_daily_price_range(
            access_token,
            ticker,
            collection_date,
            collection_date,
        )

        price_data = {
            "output2": rows
        }

        df = pd.DataFrame(
            price_data["output2"]
        )

        required_columns = [
            "stck_bsop_date",
            "stck_oprc",
            "stck_hgpr",
            "stck_lwpr",
            "stck_clpr",
            "acml_vol",
            "acml_tr_pbmn",
        ]

        # --------------------------------------------------
        # 비정상 응답 확인
        # --------------------------------------------------

        missing_columns = [
            column
            for column in required_columns
            if column not in df.columns
        ]

        if missing_columns:

            print()
            print(
                "비정상 응답 - 종목 건너뜀:",
                ticker,
            )

            print(
                "필요한 컬럼:",
                required_columns,
            )

            print(
                "실제 컬럼:",
                df.columns.tolist(),
            )

            continue

        # --------------------------------------------------
        # 필요한 컬럼만 선택
        # --------------------------------------------------

        df = df[required_columns]

        # --------------------------------------------------
        # 컬럼명 변경
        # --------------------------------------------------

        df = df.rename(
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

        # --------------------------------------------------
        # ticker 추가
        # --------------------------------------------------

        df["ticker"] = ticker

        # --------------------------------------------------
        # 데이터 타입 변환
        # --------------------------------------------------

        df["date"] = pd.to_datetime(
            df["date"],
            format="%Y%m%d",
        ).dt.date

        numeric_columns = [
            "open",
            "high",
            "low",
            "close",
            "volume",
            "trading_value",
        ]

        df[numeric_columns] = df[
            numeric_columns
        ].apply(pd.to_numeric)

        # --------------------------------------------------
        # 컬럼 순서 정리
        # --------------------------------------------------

        df = df[
            [
                "date",
                "ticker",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "trading_value",
            ]
        ]

        # --------------------------------------------------
        # 날짜 정렬
        # --------------------------------------------------

        df = df.sort_values(
            "date"
        ).reset_index(drop=True)

        print(
            "행 수:",
            len(df),
        )

        if len(df) > 0:
            print(
                "날짜:",
                df["date"].min(),
            )

        all_data.append(df)

    # --------------------------------------------------
    # 6. 수집 데이터 결합
    # --------------------------------------------------

    if not all_data:
        print()
        print("수집된 데이터가 없습니다.")
        print(
            "휴장일이거나 수집 가능한 데이터가 없을 수 있습니다."
        )
        return

    final_df = pd.concat(
        all_data,
        ignore_index=True,
    )

    final_df = final_df.sort_values(
        ["ticker", "date"]
    ).reset_index(drop=True)

    # --------------------------------------------------
    # 7. 기본 검증
    # --------------------------------------------------

    print()
    print("=== 데이터 검증 ===")

    print(
        "전체 행 수:",
        len(final_df),
    )

    print(
        "종목 수:",
        final_df["ticker"].nunique(),
    )

    print(
        "수집 날짜:",
        final_df["date"].min(),
    )

    missing_count = (
        final_df.isnull()
        .sum()
        .sum()
    )

    print(
        "결측값 수:",
        missing_count,
    )

    duplicate_count = final_df.duplicated(
        subset=["ticker", "date"]
    ).sum()

    print(
        "중복 행 수:",
        duplicate_count,
    )

    # --------------------------------------------------
    # 8. 결과 출력
    # --------------------------------------------------

    print()
    print("=== 수집 결과 ===")
    print(final_df.head())

    print()
    print(
        "처리 완료:",
        len(final_df),
        "rows",
    )

if __name__ == "__main__":
    run_eod_collection(
        batch_start=0,
        batch_size=50,
    )