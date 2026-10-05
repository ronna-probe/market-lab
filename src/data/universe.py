import os
import ssl
import urllib.request
import zipfile

import pandas as pd


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# KIS 공식 KOSPI master 고정폭 필드 길이
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


# KIS 공식 KOSPI master 필드명
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


def download_kospi_master(base_dir):
    """KIS KOSPI master 파일을 다운로드한다."""

    ssl._create_default_https_context = (
        ssl._create_unverified_context
    )

    zip_path = os.path.join(
        base_dir,
        "kospi_code.zip",
    )

    master_path = os.path.join(
        base_dir,
        "kospi_code.mst",
    )

    url = (
        "https://new.real.download.dws.co.kr/"
        "common/master/kospi_code.mst.zip"
    )

    print("KOSPI master 파일 다운로드 중...")

    urllib.request.urlretrieve(
        url,
        zip_path,
    )

    with zipfile.ZipFile(zip_path) as kospi_zip:
        kospi_zip.extractall(base_dir)

    if os.path.exists(zip_path):
        os.remove(zip_path)

    return master_path


def load_kospi_master(base_dir):
    """KIS KOSPI master 파일을 DataFrame으로 변환한다."""

    master_path = download_kospi_master(base_dir)

    part1_path = os.path.join(
        base_dir,
        "kospi_code_part1.tmp",
    )

    part2_path = os.path.join(
        base_dir,
        "kospi_code_part2.tmp",
    )

    # KIS master 파일은 CP949 인코딩이다.
    with open(
        master_path,
        mode="r",
        encoding="cp949",
    ) as source:

        with open(
            part1_path,
            mode="w",
            encoding="cp949",
        ) as part1:

            with open(
                part2_path,
                mode="w",
                encoding="cp949",
            ) as part2:

                for row in source:

                    # 앞부분:
                    # 단축코드 / 표준코드 / 한글명
                    front = row[
                        0 : len(row) - 228
                    ]

                    # 뒷부분:
                    # 고정폭 분류 및 기타 정보
                    back = row[-228:]

                    short_code = front[
                        0:9
                    ].rstrip()

                    standard_code = front[
                        9:21
                    ].rstrip()

                    name = front[
                        21:
                    ].strip()

                    part1.write(
                        short_code
                        + ","
                        + standard_code
                        + ","
                        + name
                        + "\n"
                    )

                    part2.write(back)

    # 종목코드 / 표준코드 / 종목명
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

    # 고정폭 분류 정보
    df2 = pd.read_fwf(
        part2_path,
        widths=FIELD_SPECS,
        names=FIELD_NAMES,
        dtype=str,
        encoding="cp949",
    )

    # 앞부분 + 뒷부분 결합
    df = pd.concat(
        [
            df1.reset_index(drop=True),
            df2.reset_index(drop=True),
        ],
        axis=1,
    )

    # 임시 파일 삭제
    for path in [
        master_path,
        part1_path,
        part2_path,
    ]:
        if os.path.exists(path):
            os.remove(path)

    return df


def clean_field(value):
    """master 필드 값을 비교하기 쉽게 정리한다."""

    if pd.isna(value):
        return ""

    return str(value).strip().upper()


def get_kospi_tickers():
    """
    KOSPI Universe를 생성한다.

    포함:
    - 보통주
    - 우선주

    제외:
    - ETF
    - ETN
    - REIT
    - 펀드
    - ELW
    - 신주인수권
    - 기타 비주권 상품
    - SPAC

    기준:
    - 증권그룹구분코드 == ST
    - SPAC == Y 인 종목 제외
    """

    df = load_kospi_master(BASE_DIR)

    # --------------------------------------------------
    # 1. 6자리 종목코드만 남긴다.
    # --------------------------------------------------

    df["단축코드"] = (
        df["단축코드"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    ticker_mask = (
        df["단축코드"]
        .str.fullmatch(r"\d{6}")
    )

    df = df[ticker_mask].copy()

    total_count = len(df)

    # --------------------------------------------------
    # 2. 증권그룹구분코드 정리
    #
    # KIS 공식 정의:
    #
    # ST = 주권
    # MF = 증권투자회사
    # RT = 부동산투자회사
    # SC = 선박투자회사
    # IF = 사회간접자본투융자회사
    # DR = 주식예탁증서
    # EW = ELW
    # EF = ETF
    # SW = 신주인수권증권
    # SR = 신주인수권증서
    # BC = 수익증권
    # FE = 해외ETF
    # FS = 외국주권
    #
    # 따라서 ST만 남기면
    # 일반 주식 + 우선주만 남는다.
    # --------------------------------------------------

    df["증권그룹구분코드_clean"] = (
        df["그룹코드"]
        .apply(clean_field)
    )

    stock_mask = (
        df["증권그룹구분코드_clean"]
        == "ST"
    )

    non_stock_count = int(
        (~stock_mask).sum()
    )

    df = df[stock_mask].copy()

    # --------------------------------------------------
    # 3. SPAC 제외
    # --------------------------------------------------

    df["SPAC_clean"] = (
        df["SPAC"]
        .apply(clean_field)
    )

    spac_mask = (
        df["SPAC_clean"]
        == "Y"
    )

    spac_count = int(
        spac_mask.sum()
    )

    df = df[~spac_mask].copy()

    # --------------------------------------------------
    # 4. 우선주 개수 확인
    #
    # 0 = 보통주
    # 1 = 구형우선주
    # 2 = 신형우선주
    #
    # 우선주는 제외하지 않는다.
    # --------------------------------------------------

    df["preferred_clean"] = (
        df["우선주"]
        .apply(clean_field)
    )

    preferred_mask = (
        df["preferred_clean"].isin(
            [
                "1",
                "2",
            ]
        )
    )

    preferred_count = int(
        preferred_mask.sum()
    )

    # --------------------------------------------------
    # 5. 최종 Universe 생성
    # --------------------------------------------------

    tickers = (
        df["단축코드"]
        .tolist()
    )

    # --------------------------------------------------
    # 6. 결과 출력
    # --------------------------------------------------

    print()
    print("========================================")
    print("KOSPI Universe 생성 성공")
    print("========================================")

    print(
        "전체 6자리 종목 수:",
        total_count,
    )

    print(
        "주권(ST) 이외 제외:",
        non_stock_count,
    )

    print(
        "SPAC 제외:",
        spac_count,
    )

    print(
        "최종 종목 수:",
        len(tickers),
    )

    print(
        "우선주 수:",
        preferred_count,
    )

    print()
    print("앞 20개:")
    print(tickers[:20])

    return tickers


if __name__ == "__main__":
    get_kospi_tickers()