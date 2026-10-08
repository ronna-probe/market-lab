import pandas as pd

from datetime import datetime
from zoneinfo import ZoneInfo

from src.data.kis import get_daily_price


KST = ZoneInfo("Asia/Seoul")


def check_eod_time():
    """EOD 데이터 수집 가능 시간 확인"""
    now = datetime.now(KST)

    if now.hour < 16:
        raise RuntimeError(
            "EOD 데이터 수집은 16:00 이후에만 가능합니다. "
            f"현재 시각: {now.strftime('%Y-%m-%d %H:%M:%S')}"
        )


def process_price_data(price_data, ticker):
    """KIS 응답을 검증하고 BigQuery 적재용 DataFrame으로 변환한다."""
    required_columns = [
        "stck_bsop_date",
        "stck_oprc",
        "stck_hgpr",
        "stck_lwpr",
        "stck_clpr",
        "acml_vol",
        "acml_tr_pbmn",
    ]

    df = pd.DataFrame(price_data["output2"])

    if df.empty:
        raise RuntimeError("거래 데이터 없음")

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise RuntimeError(
            f"필수 컬럼 누락: {missing_columns}"
        )

    if df["stck_bsop_date"].isna().all():
        raise RuntimeError("거래일 없음")

    df = df[required_columns].rename(
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

    numeric_columns = [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "trading_value",
    ]

    df[numeric_columns] = df[numeric_columns].apply(
        pd.to_numeric,
        errors="coerce",
    )

    # EOD 데이터 품질 검증
    if df["close"].isna().any() or (df["close"] <= 0).any():
        raise RuntimeError("유효하지 않은 종가")

    if df["volume"].isna().any() or (df["volume"] < 0).any():
        raise RuntimeError("유효하지 않은 거래량")

    if (
        (df["high"] < df["open"]).any()
        or (df["high"] < df["close"]).any()
        or (df["low"] > df["open"]).any()
        or (df["low"] > df["close"]).any()
        or (df["high"] < df["low"]).any()
    ):
        raise RuntimeError("비정상 OHLC 데이터")

    df["date"] = pd.to_datetime(
        df["date"],
        format="%Y%m%d",
    ).dt.date

    df["ticker"] = ticker

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

    df = df.sort_values(
        "date"
    ).reset_index(drop=True)

    return df


def collect_daily_prices(
    access_token,
    tickers,
    batch_start=0,
    batch_size=100,
):
    # 1. EOD 수집 기준일 및 실행 시간 확인
    check_eod_time()

    now = datetime.now(KST)
    today = now.strftime("%Y%m%d")

    print()
    print("EOD 수집 기준일:", today)

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

    # 2. 1차 수집
    all_data = []
    success_tickers = []
    failed_tickers = []

    for ticker in batch_tickers:
        print()
        print("데이터 수집:", ticker)

        try:
            price_data = get_daily_price(
                access_token,
                ticker,
                today,
                today,
            )

            df = process_price_data(
                price_data,
                ticker,
            )

        except Exception as e:
            print()
            print("ERROR:", ticker)
            print("오류 내용:", repr(e))

            failed_tickers.append({
                "ticker": ticker,
                "error": repr(e),
            })

            continue

        print("행 수:", len(df))
        print("날짜:", df["date"].min())

        success_tickers.append(ticker)
        all_data.append(df)

    # 3. 실패 종목 1회 재시도
    if failed_tickers:
        retry_tickers = [
            item["ticker"]
            for item in failed_tickers
        ]

        print()
        print("=" * 40)
        print("실패 종목 재시도")
        print("재시도 종목 수:", len(retry_tickers))
        print("=" * 40)

        retry_failed_tickers = []

        for ticker in retry_tickers:
            print()
            print("재시도:", ticker)

            try:
                price_data = get_daily_price(
                    access_token,
                    ticker,
                    today,
                    today,
                )

                df = process_price_data(
                    price_data,
                    ticker,
                )

            except Exception as e:
                print()
                print("재시도 실패:", ticker)
                print("오류 내용:", repr(e))

                retry_failed_tickers.append({
                    "ticker": ticker,
                    "error": repr(e),
                })

                continue

            print("재시도 성공:", ticker)
            print("행 수:", len(df))
            print("날짜:", df["date"].min())

            success_tickers.append(ticker)
            all_data.append(df)

        failed_tickers = retry_failed_tickers

    # 4. 최종 데이터 확인
    if not all_data:
        raise RuntimeError("수집된 데이터가 없습니다.")

    df = pd.concat(
        all_data,
        ignore_index=True,
    )

    df = df.sort_values(
        ["ticker", "date"]
    ).reset_index(drop=True)

    print()
    print("EOD 데이터 수집 완료")
    print("대상 종목 수:", len(batch_tickers))
    print("성공 종목 수:", len(success_tickers))
    print("최종 실패 종목 수:", len(failed_tickers))
    print("전체 행 수:", len(df))

    if failed_tickers:
        print()
        print("최종 실패 종목:")

        for item in failed_tickers:
            print(
                item["ticker"],
                "-",
                item["error"],
            )

    return df
