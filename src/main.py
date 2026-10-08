import os

from src.collect.eod import collect_daily_prices
from src.storage.bigquery import save_daily_stock_price


def main():
    # GitHub Actions에서 배치 범위를 환경변수로 전달받는다.
    batch_start = int(os.getenv("BATCH_START", "0"))
    batch_size = int(os.getenv("BATCH_SIZE", "100"))

    df = collect_daily_prices(
        batch_start=batch_start,
        batch_size=batch_size,
    )

    save_daily_stock_price(df)


if __name__ == "__main__":
    main()