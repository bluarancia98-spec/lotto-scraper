import urllib.request
import json
import os
from datetime import datetime, timezone, timedelta

# 동행복권 공식 API URL
LOTTO_API_URL = "https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo="

def fetch_lotto_data(round_no):
    """API를 호출하여 특정 회차의 데이터를 가져옵니다."""
    url = f"{LOTTO_API_URL}{round_no}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"[Error] 통신 오류: {e}")
    return None

def main():
    print("동행복권 최신 당첨 데이터 수집을 시작합니다...")
    
    # 한국 표준시(KST) 설정
    kst = timezone(timedelta(hours=9))
    now_kst = datetime.now(kst)
    
    # 1회차 기준일 (2002년 12월 7일)
    base_date = datetime(2002, 12, 7, tzinfo=kst)
    
    # 현재 날짜 기준으로 예상 회차 자동 계산 (5월 30일 기준 1226회 도출)
    days_passed = (now_kst - base_date).days
    current_round = (days_passed // 7) + 1

    target_round = current_round
    valid_data = None

    # 최대 5주 전까지 역추적하며 실제 '추첨 완료' 데이터가 있는지 확실하게 검증
    for _ in range(5):
        data = fetch_lotto_data(target_round)
        if data and data.get("returnValue") == "success":
            valid_data = data
            break
        else:
            print(f"{target_round}회차 데이터가 아직 없습니다. 이전 회차로 이동합니다.")
            target_round -= 1

    if not valid_data:
        print("[Error] 유효한 로또 데이터를 찾을 수 없습니다.")
        return

    print(f"✅ 최종 확인된 최신 회차: {valid_data['drwNo']}회")

    # 앱에서 즉시 사용할 수 있도록 완벽하게 파싱된 데이터 구조
    formatted_data = {
        "drawNo": valid_data["drwNo"],
        "drawDate": valid_data["drwNoDate"],
        "winningNumbers": [
            valid_data["drwtNo1"], valid_data["drwtNo2"], valid_data["drwtNo3"],
            valid_data["drwtNo4"], valid_data["drwtNo5"], valid_data["drwtNo6"]
        ],
        "bonusNumber": valid_data["bnusNo"],
        "firstPrizeAmount": valid_data["firstWinamnt"],
        "firstPrizeWinners": valid_data["firstPrzwnerCo"],
        "updateTime": now_kst.strftime("%Y-%m-%d %H:%M:%S (KST)")
    }

    # data 폴더 안전 생성
    os.makedirs("data", exist_ok=True)
    
    # 1. 1226.json 등 개별 회차 파일 생성
    filename = f"data/{valid_data['drwNo']}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(formatted_data, f, ensure_ascii=False, indent=2)
    print(f"✅ {filename} 파일 생성 완료.")

    # 2. latest.json 갱신 (앱 연동용)
    latest_filename = "data/latest.json"
    with open(latest_filename, "w", encoding="utf-8") as f:
        json.dump(formatted_data, f, ensure_ascii=False, indent=2)
    print(f"✅ {latest_filename} 파일 갱신 완료.")

if __name__ == "__main__":
    main()
