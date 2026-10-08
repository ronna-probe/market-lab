from src.collect.eod import collect_daily_prices
from src.data.kis import get_access_token
from src.data.universe import get_kospi_tickers
from src.storage.bigquery import save_daily_stock_price


def main():
    batch_size = 100

    # Universe와 Access Token은 전체 실행에서 한 번만 생성한다.
    tickers = get_kospi_tickers()
    access_token = get_access_token()["access_token"]

    total_tickers = len(tickers)

    print()
    print("전체 실행 시작")
    print("전체 종목 수:", total_tickers)
    print("배치 크기:", batch_size)

    for batch_start in range(0, total_tickers, batch_size):
        print()
        print("=" * 40)
        print("Batch start:", batch_start)
        print("Batch size:", batch_size)
        print("=" * 40)

        df = collect_daily_prices(
            access_token=access_token,
            tickers=tickers,
            batch_start=batch_start,
            batch_size=batch_size,
        )

        save_daily_stock_price(df)

    print()
    print("전체 Batch 실행 완료")


if __name__ == "__main__":
    main()