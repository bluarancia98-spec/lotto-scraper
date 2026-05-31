import urllib.request
import json
import os
from datetime import datetime, timezone, timedelta

# 동행복권 공식 API URL
LOTTO_API_URL = "https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo="

def get_latest_drawn_round():
    """
    외부 라이브러리(pytz, requests) 없이 파이썬 내장 모듈만으로
    가장 최근에 추첨이 완료된 로또 회차 데이터를 완벽하게 찾아냅니다.
    """
    # 파이썬 내장 기능을 활용한 한국 표준시(KST) 설정
    kst = timezone(timedelta(hours=9))
    now_kst = datetime.now(kst)
    
    # 1회차 추첨일(2002년 12월 7일) 기준
    reference_date = datetime(2002, 12, 7, tzinfo=kst)
    
    # 경과 일수를 7일로 나누어 현재 예상 회차 계산
    days_passed = (now_kst - reference_date).days
    estimated_round = (days_passed // 7) + 1

    target_round = estimated_round

    # 최대 5주 전까지 역추적하며 실제 '추첨 완료' 데이터가 있는지 검증
    for _ in range(5):
        try:
            url = f"{LOTTO_API_URL}{target_round}"
            # urllib를 사용하여 외부 라이브러리(requests) 없이 통신
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    
                    # 'success' 반환 시 (실제 당첨 결과가 발표된 회차)
                    if data.get("returnValue") == "success":
                        return data
                        
            # 'fail' 반환 시 (아직 미추첨) -> 회차를 -1 하여 이전 회차 재검색
            target_round -= 1
        except Exception as e:
            print(f"[Error] 통신 중 오류 발생: {e}")
            target_round -= 1

    return None

def main():
    print("동행복권 최신 당첨 데이터 수집을 시작합니다 (종속성 제로 버전)...")
    data = get_latest_drawn_round()
    
    if not data:
        print("[Error] 유효한 로또 데이터를 가져오지 못했습니다.")
        return

    draw_no = data["drwNo"]
    
    # KST 기준 현재 시간 (깃허브 액션 무조건 업데이트 유발용)
    kst = timezone(timedelta(hours=9))
    now_kst = datetime.now(kst).strftime("%Y-%m-%d %H:%M:%S")
    
    # 앱에서 즉시 사용할 수 있도록 완벽하게 파싱된 데이터 구조
    formatted_data = {
        "drawNo": draw_no,
        "drawDate": data["drwNoDate"],
        "winningNumbers": [
            data["drwtNo1"],
            data["drwtNo2"],
            data["drwtNo3"],
            data["drwtNo4"],
            data["drwtNo5"],
            data["drwtNo6"]
        ],
        "bonusNumber": data["bnusNo"],
        "firstPrizeAmount": data["firstWinamnt"],
        "firstPrizeWinners": data["firstPrzwnerCo"],
        "stores": [],
        "updateTime": f"{now_kst} (KST)"
    }

    # data 폴더 안전 생성
    os.makedirs("data", exist_ok=True)
    
    # 1. 1225.json 등 개별 회차 파일 생성
    filename = f"data/{draw_no}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(formatted_data, f, ensure_ascii=False, indent=2)
    print(f"[Success] {filename} 파일이 성공적으로 생성되었습니다.")

    # 2. latest.json 갱신 (앱 연동용)
    latest_filename = "data/latest.json"
    with open(latest_filename, "w", encoding="utf-8") as f:
        json.dump(formatted_data, f, ensure_ascii=False, indent=2)
    print(f"[Success] {latest_filename} 파일에 최신 데이터가 반영되었습니다.")

if __name__ == "__main__":
    main()
