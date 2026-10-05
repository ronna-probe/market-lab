import pandas as pd
from google.cloud import bigquery


PROJECT_ID = "backtest-510311"
TABLE_ID = f"{PROJECT_ID}.market_data.daily_stock_price"


def save_daily_stock_price(df: pd.DataFrame):
    """
    일봉 데이터를 BigQuery에 저장한다.

    동일한 (ticker, date)가 이미 존재하면 건너뛰고,
    존재하지 않는 데이터만 INSERT한다.
    """

    client = bigquery.Client()

    temp_table_id = f"{TABLE_ID}_temp"

    # 1. 임시 테이블 적재
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    job = client.load_table_from_dataframe(
        df,
        temp_table_id,
        job_config=job_config,
    )

    job.result()

    # 2. 기존 데이터는 유지하고 새로운 데이터만 INSERT
    merge_query = f"""
    MERGE `{TABLE_ID}` AS target
    USING `{temp_table_id}` AS source

    ON target.ticker = source.ticker
    AND target.date = source.date

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

    # 3. 임시 테이블 삭제
    client.delete_table(
        temp_table_id,
        not_found_ok=True,
    )

    print()
    print("BigQuery 적재 성공")
    print("테이블:", TABLE_ID)
    print("처리 행 수:", len(df))