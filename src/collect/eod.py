import pandas as pd

from datetime import datetime
from zoneinfo import ZoneInfo

from src.data.kis import get_access_token, get_daily_price
from src.data.universe import get_kospi_tickers


KST = ZoneInfo("Asia/Seoul")


def check_eod_time():
    """EOD 데이터 수집 가능 시간 확인"""
    now = datetime.now(KST)

    if now.hour < 16:
        raise RuntimeError(
            "EOD 데이터 수집은 16:00 이후에만 가능합니다. "
            f"현재 시각: {now.strftime('%Y-%m-%d %H:%M:%S')}"
        )


def collect_daily_prices(batch_start=0, batch_size=50):
    # 1. EOD 수집 기준일 및 실행 시간 확인
    # check_eod_time()

    now = datetime.now(KST)
    today = now.strftime("%Y%m%d")

    print()
    print("EOD 수집 기준일:", today)

    # 2. KIS 인증 및 종목 Universe 생성
    result = get_access_token()
    access_token = result["access_token"]

    print()
    print("KIS Access Token 발급 성공")

    tickers = get_kospi_tickers()

    print()
    print("KOSPI 종목 Universe 생성 성공")
    print("전체 종목 수:", len(tickers))
    print("앞 10개:", tickers[:10])

    # 테스트 및 배치 실행을 위한 종목 범위
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

    # 3. 종목별 EOD 데이터 수집 및 정제
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

        except Exception as e:
            print()
            print("ERROR:", ticker)
            print("오류 내용:", repr(e))

            failed_tickers.append({
                "ticker": ticker,
                "error": repr(e),
            })

            continue

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
            print()
            print("거래 데이터 없음 - 종목 건너뜀:", ticker)
            continue

        missing_columns = [
            column
            for column in required_columns
            if column not in df.columns
        ]

        if missing_columns:
            print()
            print("비정상 응답 - 종목 건너뜀:", ticker)
            print("실제 컬럼:", df.columns.tolist())
            continue

        if df["stck_bsop_date"].isna().all():
            print()
            print("거래일 없음 - 종목 건너뜀:", ticker)
            continue

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
            print()
            print("유효하지 않은 종가 - 종목 건너뜀:", ticker)
            continue

        if df["volume"].isna().any() or (df["volume"] < 0).any():
            print()
            print("유효하지 않은 거래량 - 종목 건너뜀:", ticker)
            continue

        if (
            (df["high"] < df["open"]).any()
            or (df["high"] < df["close"]).any()
            or (df["low"] > df["open"]).any()
            or (df["low"] > df["close"]).any()
            or (df["high"] < df["low"]).any()
        ):
            print()
            print("비정상 OHLC 데이터 - 종목 건너뜀:", ticker)
            continue

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

        df = df.sort_values("date").reset_index(drop=True)

        print("행 수:", len(df))
        print("날짜:", df["date"].min())

        success_tickers.append(ticker)
        all_data.append(df)

    # 4. 전체 종목 데이터 결합 및 최종 정렬
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
    print("실패 종목 수:", len(failed_tickers))
    print("전체 행 수:", len(df))

    if failed_tickers:
        print()
        print("실패 종목:")

        for item in failed_tickers:
            print(
                item["ticker"],
                "-",
                item["error"],
            )

    return df

if __name__ == "__main__":
    collect_daily_prices()
