import urllib.request
import urllib.parse
import json
import os
import sys
from datetime import datetime, timezone, timedelta

LOTTO_API_URL = "https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo="

def fetch_data(round_no):
    """3중 우회 방식을 사용하여 동행복권 API 데이터를 확실하게 가져옵니다."""
    url = f"{LOTTO_API_URL}{round_no}"
    encoded_url = urllib.parse.quote(url)
    
    # 일반적인 한국 브라우저로 위장하는 헤더
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
    }

    # 접속 시도 경로 1: 다이렉트 통신 (가끔 차단이 풀릴 때를 대비)
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get("returnValue") == "success":
                print("[Success] 다이렉트 서버 접속 성공")
                return data
    except Exception as e:
        print(f"[Info] 다이렉트 접속 차단됨 (GitHub IP 밴): {e}")

    # 접속 시도 경로 2: AllOrigins 무료 프록시 우회
    print("[Proxy 1] 첫 번째 우회 경로를 시도합니다...")
    proxy_url_1 = f"https://api.allorigins.win/raw?url={encoded_url}"
    try:
        req = urllib.request.Request(proxy_url_1, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get("returnValue") == "success":
                print("[Success] Proxy 1 (AllOrigins) 우회 접속 성공!")
                return data
    except Exception as e:
        print(f"[Info] Proxy 1 우회 실패: {e}")

    # 접속 시도 경로 3: CorsProxy 우회 (최후의 보루)
    print("[Proxy 2] 두 번째 우회 경로를 시도합니다...")
    proxy_url_2 = f"https://corsproxy.io/?{encoded_url}"
    try:
        req = urllib.request.Request(proxy_url_2, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get("returnValue") == "success":
                print("[Success] Proxy 2 (CorsProxy) 우회 접속 성공!")
                return data
    except Exception as e:
        print(f"[Info] Proxy 2 우회 실패: {e}")

    return None

def main():
    print("🚀 동행복권 최신 당첨 데이터 수집 시작 (프록시 우회 모드)")
    kst = timezone(timedelta(hours=9))
    base_date = datetime(2002, 12, 7, tzinfo=kst)
    today = datetime.now(kst)
    
    # 5월 30일 기준 1226회차 자동 계산
    current_round = ((today - base_date).days // 7) + 1
    print(f"🎯 타겟 회차: {current_round}회")

    # 데이터 우회 수집 실행
    data = fetch_data(current_round)

    if not data:
        print(f"[Error] 모든 우회 경로가 막혔거나, {current_round}회차 데이터가 아직 없습니다.")
        sys.exit(1) # 확실하게 에러 처리하여 빈 껍데기 파일 생성 방지

    # 성공적으로 가져온 데이터 구조화
    formatted_data = {
        "drawNo": data["drwNo"],
        "drawDate": data["drwNoDate"],
        "winningNumbers": [
            data["drwtNo1"], data["drwtNo2"], data["drwtNo3"],
            data["drwtNo4"], data["drwtNo5"], data["drwtNo6"]
        ],
        "bonusNumber": data["bnusNo"],
        "firstPrizeAmount": data["firstWinamnt"],
        "firstPrizeWinners": data["firstPrzwnerCo"],
        "updateTime": datetime.now(kst).strftime("%Y-%m-%d %H:%M:%S (KST)")
    }

    os.makedirs("data", exist_ok=True)
    
    filename = f"data/{data['drwNo']}.json"
    latest_filename = "data/latest.json"
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(formatted_data, f, ensure_ascii=False, indent=2)
        
    with open(latest_filename, "w", encoding="utf-8") as f:
        json.dump(formatted_data, f, ensure_ascii=False, indent=2)
        
    print(f"✅ {current_round}회차 데이터 추출 및 파일 생성 완료!")

if __name__ == "__main__":
    main()
