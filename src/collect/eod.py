import pandas as pd

from datetime import datetime
from zoneinfo import ZoneInfo

from src.data.kis import get_daily_price


KST = ZoneInfo("Asia/Seoul")


def process_price_data(price_data, ticker):
    """KIS ?‘ë‹µ??ê²€ì¦í•˜ê³?BigQuery ?ì¬??DataFrame?¼ë¡œ ë³€?˜í•œ??"""
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
        raise RuntimeError("ê±°ë˜ ?°ì´???†ìŒ")

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise RuntimeError(
            f"?„ìˆ˜ ì»¬ëŸ¼ ?„ë½: {missing_columns}"
        )

    if df["stck_bsop_date"].isna().all():
        raise RuntimeError("ê±°ë˜???†ìŒ")

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

    # EOD ?°ì´???ˆì§ˆ ê²€ì¦?
    if df["close"].isna().any() or (df["close"] <= 0).any():
        raise RuntimeError("? íš¨?˜ì? ?Šì? ì¢…ê?")

    if df["volume"].isna().any() or (df["volume"] < 0).any():
        raise RuntimeError("? íš¨?˜ì? ?Šì? ê±°ë˜??)

    if (
        (df["high"] < df["open"]).any()
        or (df["high"] < df["close"]).any()
        or (df["low"] > df["open"]).any()
        or (df["low"] > df["close"]).any()
        or (df["high"] < df["low"]).any()
    ):
        raise RuntimeError("ë¹„ì •??OHLC ?°ì´??)

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

    # 1. EOD ?˜ì§‘ ê¸°ì???ë°??¤í–‰ ?œê°„ ?•ì¸
    # check_eod_time()


    # 1. EOD ?˜ì§‘ ê¸°ì????•ì¸

    now = datetime.now(KST)
    today = now.strftime("%Y%m%d")

    print()
    print("EOD ?˜ì§‘ ê¸°ì???", today)

    batch_tickers = tickers[
        batch_start:batch_start + batch_size
    ]

    print()
    print("?˜ì§‘ ?€??ì¢…ëª© ??", len(batch_tickers))
    print(
        "Batch ë²”ìœ„:",
        batch_start,
        "~",
        batch_start + len(batch_tickers) - 1,
    )

    # 2. 1ì°??˜ì§‘
    all_data = []
    success_tickers = []
    failed_tickers = []

    for ticker in batch_tickers:
        print()
        print("?°ì´???˜ì§‘:", ticker)

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
            print("?¤ë¥˜ ?´ìš©:", repr(e))

            failed_tickers.append({
                "ticker": ticker,
                "error": repr(e),
            })

            continue

        print("????", len(df))
        print("? ì§œ:", df["date"].min())

        success_tickers.append(ticker)
        all_data.append(df)

    # 3. ?¤íŒ¨ ì¢…ëª© 1???¬ì‹œ??
    if failed_tickers:
        retry_tickers = [
            item["ticker"]
            for item in failed_tickers
        ]

        print()
        print("=" * 40)
        print("?¤íŒ¨ ì¢…ëª© ?¬ì‹œ??)
        print("?¬ì‹œ??ì¢…ëª© ??", len(retry_tickers))
        print("=" * 40)

        retry_failed_tickers = []

        for ticker in retry_tickers:
            print()
            print("?¬ì‹œ??", ticker)

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
                print("?¬ì‹œ???¤íŒ¨:", ticker)
                print("?¤ë¥˜ ?´ìš©:", repr(e))

                retry_failed_tickers.append({
                    "ticker": ticker,
                    "error": repr(e),
                })

                continue

            print("?¬ì‹œ???±ê³µ:", ticker)
            print("????", len(df))
            print("? ì§œ:", df["date"].min())

            success_tickers.append(ticker)
            all_data.append(df)

        failed_tickers = retry_failed_tickers

    # 4. ìµœì¢… ?°ì´???•ì¸
    if not all_data:
        raise RuntimeError("?˜ì§‘???°ì´?°ê? ?†ìŠµ?ˆë‹¤.")

    df = pd.concat(
        all_data,
        ignore_index=True,
    )

    df = df.sort_values(
        ["ticker", "date"]
    ).reset_index(drop=True)

    print()
    print("EOD ?°ì´???˜ì§‘ ?„ë£Œ")
    print("?€??ì¢…ëª© ??", len(batch_tickers))
    print("?±ê³µ ì¢…ëª© ??", len(success_tickers))
    print("ìµœì¢… ?¤íŒ¨ ì¢…ëª© ??", len(failed_tickers))
    print("?„ì²´ ????", len(df))

    if failed_tickers:
        print()
        print("ìµœì¢… ?¤íŒ¨ ì¢…ëª©:")

        for item in failed_tickers:
            print(
                item["ticker"],
                "-",
                item["error"],
            )

    return df
