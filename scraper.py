import urllib.request
import json
import os
import sys
from datetime import datetime, timezone, timedelta

LOTTO_API_URL = "https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo="

def main():
    print("동행복권 최신 당첨 데이터 수집을 시작합니다...")
    kst = timezone(timedelta(hours=9))
    base_date = datetime(2002, 12, 7, tzinfo=kst)
    today = datetime.now(kst)
    
    # 5월 30일 기준 1226회차 정확히 타겟팅
    current_round = ((today - base_date).days // 7) + 1
    print(f"[Info] 타겟 회차: {current_round}회")

    url = f"{LOTTO_API_URL}{current_round}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"[Error] 동행복권 서버 접속 실패 (통신 오류): {e}")
        sys.exit(1) # 데이터 없으면 깃허브 액션 강제 실패 처리

    # API는 응답했으나 아직 당첨 번호가 업데이트되지 않은 경우
    if data.get("returnValue") != "success":
        print(f"[Error] 동행복권 서버에 {current_round}회차 데이터가 아직 없습니다. API 지연 중입니다.")
        sys.exit(1) # 거짓 성공(Green) 방지를 위해 강제 실패 처리

    print(f"✅ {current_round}회차 데이터 로드 성공!")

    # 데이터 구조화
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
    
    # 개별 파일 및 latest.json 생성
    filename = f"data/{data['drwNo']}.json"
    latest_filename = "data/latest.json"
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(formatted_data, f, ensure_ascii=False, indent=2)
        
    with open(latest_filename, "w", encoding="utf-8") as f:
        json.dump(formatted_data, f, ensure_ascii=False, indent=2)
        
    print(f"✅ 데이터 저장 완료. GitHub Actions가 커밋을 진행합니다.")

if __name__ == "__main__":
    main()
