from src.data.kis import (
    get_access_token,
    get_daily_price,
    get_daily_price_range,  # backfill
)

import pandas as pd
from google.cloud import bigquery


def main():
    # 1. KIS API 인증
    result = get_access_token()
    access_token = result["access_token"]

    # 2. 수집할 종목
    tickers = [
        "005930",  # 삼성전자
        "000660",  # SK하이닉스
    ]

    # 3. 조회 기간
    start_date = "20210101"
    end_date = "20261001"

    # 4. 종목별 데이터 수집
    all_data = []

    for ticker in tickers:
        print()
        print("데이터 수집:", ticker)

        """
        price_data = get_daily_price(
            access_token,
            ticker,
            start_date,
            end_date,
        )
        """

        # backfill
        rows = get_daily_price_range(
            access_token,
            ticker,
            start_date,
            end_date,
        )
        
        price_data = {
            "output2": rows
        }

        df = pd.DataFrame(price_data["output2"])

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

        df["ticker"] = ticker

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

        df[numeric_columns] = df[numeric_columns].apply(
            pd.to_numeric
        )

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

        df = df.sort_values("date").reset_index(drop=True)

        print("행 수:", len(df))
        print("API 반환 행 수:", len(price_data["output2"]))
        print(
            "API 날짜 범위:",
            price_data["output2"][-1]["stck_bsop_date"],
            "~",
            price_data["output2"][0]["stck_bsop_date"],
        )
        print(
            "날짜 범위:",
            df["date"].min(),
            "~",
            df["date"].max(),
        )

        all_data.append(df)

    # 5. 여러 종목 데이터를 하나로 결합
    df = pd.concat(
        all_data,
        ignore_index=True,
    )

    # 6. 전체 데이터 정렬
    df = df.sort_values(
        ["ticker", "date"]
    ).reset_index(drop=True)

    # 7. 데이터 검증
    print()
    print("전체 데이터 수집 및 정제 성공")
    print("종목 수:", df["ticker"].nunique())
    print("전체 행 수:", len(df))

    print()
    print("종목별 행 수:")
    print(df.groupby("ticker").size())

    print()
    print("결측치:")
    print(df.isna().sum())

    print()
    print(
        "중복:",
        df.duplicated(
            subset=["ticker", "date"]
        ).sum(),
    )

    # 8. BigQuery 연결
    client = bigquery.Client()

    # 9. BigQuery 테이블
    project_id = "backtest-510311"
    table_id = f"{project_id}.market_data.daily_stock_price"

    # 10. 임시 테이블 생성
    temp_table_id = f"{table_id}_temp"

    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    job = client.load_table_from_dataframe(
        df,
        temp_table_id,
        job_config=job_config,
    )

    job.result()

    # 11. MERGE
    merge_query = f"""
    MERGE `{table_id}` AS target
    USING `{temp_table_id}` AS source

    ON target.ticker = source.ticker
    AND target.date = source.date
    AND target.date BETWEEN DATE('{df["date"].min()}')
                        AND DATE('{df["date"].max()}')

    WHEN MATCHED THEN
      UPDATE SET
        open = source.open,
        high = source.high,
        low = source.low,
        close = source.close,
        volume = source.volume,
        trading_value = source.trading_value

    WHEN NOT MATCHED THEN
      INSERT (
        date,
        ticker,
        open,
        high,
        low,
        close,
        volume,
        trading_value
      )
      VALUES (
        source.date,
        source.ticker,
        source.open,
        source.high,
        source.low,
        source.close,
        source.volume,
        source.trading_value
      )
    """

    query_job = client.query(merge_query)
    query_job.result()

    # 12. 임시 테이블 삭제
    client.delete_table(
        temp_table_id,
        not_found_ok=True,
    )

    print()
    print("BigQuery 적재 성공")
    print("테이블:", table_id)
    print("처리 행 수:", len(df))


if __name__ == "__main__":
    main()
