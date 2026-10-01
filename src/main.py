from src.data.kis import get_access_token, get_daily_price

import pandas as pd
from google.cloud import bigquery


def main():
    # 1. KIS API 인증
    result = get_access_token()
    access_token = result["access_token"]

    # 2. 삼성전자 일봉 데이터 조회
    ticker = "005930"

    price_data = get_daily_price(
        access_token,
        ticker,
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

    # 5. ticker 컬럼 추가
    df["ticker"] = ticker

    # 6. 데이터 타입 변환
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

    # 7. 컬럼 순서 정리
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

    # 8. 날짜 기준 오름차순 정렬
    df = df.sort_values("date").reset_index(drop=True)

    # 9. 데이터 검증
    print("삼성전자 데이터 수집 및 정제 성공")
    print()
    print(df.head())
    print()
    print(df.dtypes)
    print()
    print("행 수:", len(df))

    print()
    print("결측치:")
    print(df.isna().sum())

    print()
    print("중복 날짜:", df["date"].duplicated().sum())

    print()
    print(
        "날짜 범위:",
        df["date"].min(),
        "~",
        df["date"].max(),
    )

    # 10. BigQuery 연결
    client = bigquery.Client()

    # 11. BigQuery 테이블
    project_id = "backtest-510311"
    table_id = f"{project_id}.market_data.daily_stock_price"

    # 12. 임시 테이블 생성
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
    
    # 13. MERGE로 중복 방지
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
    
    # 14. 임시 테이블 삭제
    client.delete_table(temp_table_id, not_found_ok=True)
    
    print()
    print("BigQuery 적재 성공")
    print("테이블:", table_id)
    print("처리 행 수:", len(df))


if __name__ == "__main__":
    main()
