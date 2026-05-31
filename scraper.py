import json
import os
import sys
import random
from datetime import datetime, timezone, timedelta
import cloudscraper # 봇 탐지 방화벽(WAF) 우회 라이브러리

LOTTO_API_URL = "https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo="

def generate_korean_ip():
    """한국 통신사 IP 대역을 랜덤으로 생성하여 방화벽을 기만합니다."""
    return f"211.{random.randint(100, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"

def main():
    print("🚀 [Pro Mode] 딥 웹 스크래핑 엔진 가동 (방화벽 핑거프린트 우회 시작)")
    kst = timezone(timedelta(hours=9))
    base_date = datetime(2002, 12, 7, tzinfo=kst)
    today = datetime.now(kst)
    
    # 5월 30일 기준 1226회차 정확히 타겟팅
    current_round = ((today - base_date).days // 7) + 1
    print(f"🎯 타겟 회차: {current_round}회")

    url = f"{LOTTO_API_URL}{current_round}"
    
    # 단순 파이썬 봇이 아닌, 완벽한 윈도우용 크롬 브라우저로 위장하는 세션 생성
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'mobile': False
        }
    )
    
    # 한국인 유저가 공식 홈페이지를 클릭해서 들어온 것처럼 헤더 조작
    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://dhlottery.co.kr/',
        'X-Forwarded-For': generate_korean_ip(),
        'X-Real-IP': generate_korean_ip()
    }

    try:
        print("[Info] 동행복권 서버 방화벽 우회 접속 시도 중...")
        response = scraper.get(url, headers=headers, timeout=15)
        response.raise_for_status() 
        data = response.json()
    except Exception as e:
        print(f"💥 [Error] 접속 실패 (방화벽 차단 지속 또는 통신 지연): {e}")
        sys.exit(1)

    if data.get("returnValue") != "success":
        print(f"💥 [Error] API 응답 오류 (데이터 미발표): {data}")
        sys.exit(1)

    print(f"✅ {current_round}회차 데이터 획득 성공 (방화벽 무력화 완료!)")

    # 앱 연동용 JSON 포맷팅
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
        
    print(f"✅ 데이터 저장 완료. GitHub Actions가 커밋을 시작합니다.")

if __name__ == "__main__":
    main()
