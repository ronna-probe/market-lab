from src.collect.eod import collect_daily_prices
from src.data.kis import get_access_token, check_trading_day
from src.data.universe import get_kospi_tickers
from src.storage.bigquery import save_daily_stock_price


def main():
    batch_size = 100

    # KIS Access Token은 전체 실행에서 한 번만 발급한다.
    access_token = get_access_token()["access_token"]

    # 오늘이 국내주식 거래일인지 먼저 확인한다.
    from datetime import datetime
    from zoneinfo import ZoneInfo

    today = datetime.now(
        ZoneInfo("Asia/Seoul")
    ).strftime("%Y%m%d")

    holiday_info = check_trading_day(
        access_token,
        today,
    )

    print()
    print("거래일 확인:", holiday_info)

    if holiday_info.get("opnd_yn") != "Y":
        print()
        print("오늘은 국내주식 개장일이 아닙니다.")
        print("EOD 수집을 종료합니다.")
        return

    # 거래일인 경우에만 Universe를 조회한다.
    tickers = get_kospi_tickers()

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