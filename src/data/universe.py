import os
import ssl
import urllib.request
import zipfile

import pandas as pd


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MASTER_URL = (
    "https://new.real.download.dws.co.kr/"
    "common/master/kospi_code.mst.zip"
)

FIELD_SPECS = [
    2, 1, 4, 4, 4,
    1, 1, 1, 1, 1,
    1, 1, 1, 1, 1,
    1, 1, 1, 1, 1,
    1, 1, 1, 1, 1,
    1, 1, 1, 1, 1,
    1, 9, 5, 5, 1,
    1, 1, 2, 1, 1,
    1, 2, 2, 2, 3,
    1, 3, 12, 12, 8,
    15, 21, 2, 7, 1,
    1, 1, 1, 1, 9,
    9, 9, 5, 9, 8,
    9, 3, 1, 1, 1,
]

FIELD_NAMES = [
    "그룹코드",
    "시가총액규모",
    "지수업종대분류",
    "지수업종중분류",
    "지수업종소분류",
    "제조업",
    "저유동성",
    "지배구조지수종목",
    "KOSPI200섹터업종",
    "KOSPI100",
    "KOSPI50",
    "KRX",
    "ETP",
    "ELW발행",
    "KRX100",
    "KRX자동차",
    "KRX반도체",
    "KRX바이오",
    "KRX은행",
    "SPAC",
    "KRX에너지화학",
    "KRX철강",
    "단기과열",
    "KRX미디어통신",
    "KRX건설",
    "Non1",
    "KRX증권",
    "KRX선박",
    "KRX섹터_보험",
    "KRX섹터_운송",
    "SRI",
    "기준가",
    "매매수량단위",
    "시간외수량단위",
    "거래정지",
    "정리매매",
    "관리종목",
    "시장경고",
    "경고예고",
    "불성실공시",
    "우회상장",
    "락구분",
    "액면변경",
    "증자구분",
    "증거금비율",
    "신용가능",
    "신용기간",
    "전일거래량",
    "액면가",
    "상장일자",
    "상장주수",
    "자본금",
    "결산월",
    "공모가",
    "우선주",
    "공매도과열",
    "이상급등",
    "KRX300",
    "KOSPI",
    "매출액",
    "영업이익",
    "경상이익",
    "당기순이익",
    "ROE",
    "기준년월",
    "시가총액",
    "그룹사코드",
    "회사신용한도초과",
    "담보대출가능",
    "대주가능",
]


def download_kospi_master():
    """KIS KOSPI 종목 마스터 파일을 다운로드한다."""

    ssl._create_default_https_context = (
        ssl._create_unverified_context
    )

    zip_path = os.path.join(
        BASE_DIR,
        "kospi_code.zip",
    )

    urllib.request.urlretrieve(
        MASTER_URL,
        zip_path,
    )

    with zipfile.ZipFile(zip_path) as zip_file:
        zip_file.extractall(BASE_DIR)

    os.remove(zip_path)


def load_kospi_master():
    """KIS KOSPI 마스터 파일을 DataFrame으로 읽는다."""

    download_kospi_master()

    master_path = os.path.join(
        BASE_DIR,
        "kospi_code.mst",
    )

    part1_path = os.path.join(
        BASE_DIR,
        "kospi_code_part1.tmp",
    )

    part2_path = os.path.join(
        BASE_DIR,
        "kospi_code_part2.tmp",
    )

    with open(
        master_path,
        "r",
        encoding="cp949",
    ) as source, open(
        part1_path,
        "w",
        encoding="cp949",
    ) as part1, open(
        part2_path,
        "w",
        encoding="cp949",
    ) as part2:

        for row in source:
            front = row[:-228]
            back = row[-228:]

            part1.write(
                front[0:9].rstrip()
                + ","
                + front[9:21].rstrip()
                + ","
                + front[21:].strip()
                + "\n"
            )

            part2.write(back)

    df1 = pd.read_csv(
        part1_path,
        header=None,
        names=[
            "단축코드",
            "표준코드",
            "한글명",
        ],
        dtype=str,
        encoding="cp949",
    )

    df2 = pd.read_fwf(
        part2_path,
        widths=FIELD_SPECS,
        names=FIELD_NAMES,
        dtype=str,
        encoding="cp949",
    )

    df = pd.concat(
        [
            df1.reset_index(drop=True),
            df2.reset_index(drop=True),
        ],
        axis=1,
    )

    for path in [
        master_path,
        part1_path,
        part2_path,
    ]:
        if os.path.exists(path):
            os.remove(path)

    return df


def get_kospi_tickers():
    """
    KOSPI 보통주와 우선주 Universe를 반환한다.

    제외:
    - ETF
    - ETN
    - REIT
    - 펀드
    - ELW
    - 신주인수권 등 비주권 상품
    - SPAC
    """

    df = load_kospi_master()

    df["단축코드"] = (
        df["단축코드"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    df["그룹코드"] = (
        df["그룹코드"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    df["SPAC"] = (
        df["SPAC"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    mask = (
        df["단축코드"].str.fullmatch(r"\d{6}")
        & (df["그룹코드"] == "ST")
        & (df["SPAC"] != "Y")
    )

    tickers = (
        df.loc[mask, "단축코드"]
        .tolist()
    )

    if not tickers:
        raise RuntimeError(
            "KOSPI Universe가 비어 있습니다."
        )

    print()
    print("KOSPI Universe 생성 성공")
    print("전체 6자리 종목 수:", len(
        df[df["단축코드"].str.fullmatch(r"\d{6}")]
    ))
    print("최종 종목 수:", len(tickers))
    print("앞 20개:", tickers[:20])

    return tickers


if __name__ == "__main__":
    get_kospi_tickers()