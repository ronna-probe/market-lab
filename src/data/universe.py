import os
import ssl
import urllib.request
import zipfile


KOSPI_MASTER_URL = (
    "https://new.real.download.dws.co.kr/"
    "common/master/kospi_code.mst.zip"
)


def get_kospi_tickers():
    """
    한국투자증권 KOSPI 종목 마스터파일을 다운로드하여
    종목코드(ticker) 목록을 반환한다.
    """

    # GitHub Actions 임시 디렉토리
    temp_dir = "/tmp/kis_master"
    os.makedirs(temp_dir, exist_ok=True)

    zip_path = os.path.join(
        temp_dir,
        "kospi_code.mst.zip",
    )

    # 1. 마스터파일 다운로드
    ssl._create_default_https_context = (
        ssl._create_unverified_context
    )

    urllib.request.urlretrieve(
        KOSPI_MASTER_URL,
        zip_path,
    )

    # 2. ZIP 압축 해제
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(temp_dir)

    # 3. 압축 해제된 mst 파일 찾기
    mst_files = [
        filename
        for filename in os.listdir(temp_dir)
        if filename.endswith(".mst")
    ]

    if not mst_files:
        raise FileNotFoundError(
            "KOSPI 마스터파일(.mst)을 찾을 수 없습니다."
        )

    mst_path = os.path.join(
        temp_dir,
        mst_files[0],
    )

    # 4. 종목코드 추출
    tickers = []

    with open(
        mst_path,
        "r",
        encoding="cp949",
    ) as f:

        for line in f:
            if len(line) < 9:
                continue

            # KIS 마스터파일의 앞 6자리가 단축 종목코드
            ticker = line[:6].strip()

            if ticker.isdigit() and len(ticker) == 6:
                tickers.append(ticker)

    # 5. 중복 제거 + 정렬
    tickers = sorted(set(tickers))

    if not tickers:
        raise ValueError(
            "KOSPI 종목코드를 하나도 찾지 못했습니다."
        )

    return tickers
