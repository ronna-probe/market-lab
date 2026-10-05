from src.collect.eod import collect_daily_prices
from src.storage.bigquery import save_daily_stock_price


def main():
    # 1. 오늘 일봉 데이터 수집
    df = collect_daily_prices()

    # 2. BigQuery 저장
    save_daily_stock_price(df)


if __name__ == "__main__":
    main()