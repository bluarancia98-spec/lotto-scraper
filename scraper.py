import requests
import json
import os
from datetime import datetime
import pytz

# 동행복권 공식 API URL
LOTTO_API_URL = "https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo="

def get_latest_drawn_round():
    """
    현재 날짜 기준으로 예상 회차를 계산한 뒤,
    동행복권 API를 찔러보고 아직 추첨 전(fail)이라면 이전 회차로 내려가며
    가장 최근에 '성공(success)'한 실제 추첨 회차를 찾습니다.
    """
    # 1회차 추첨일: 2002년 12월 7일
    reference_date = datetime(2002, 12, 7)
    now_kst = datetime.now(pytz.timezone('Asia/Seoul'))
    
    # 지나간 일수를 7일(1주일)로 나누어 현재 예상 회차 계산
    days_passed = (now_kst.replace(tzinfo=None) - reference_date).days
    estimated_round = (days_passed // 7) + 1

    target_round = estimated_round

    # 최대 5번(5주)까지 뒤로 가면서 확인 (안전장치)
    for _ in range(5):
        try:
            response = requests.get(f"{LOTTO_API_URL}{target_round}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                # API 반환값이 'success'인 경우 (실제 추첨이 완료된 데이터)
                if data.get("returnValue") == "success":
                    return data
                
            # 'fail'인 경우 (아직 추첨 전) -> 회차를 1 낮추고 다시 시도
            target_round -= 1
        except Exception as e:
            print(f"[Error] API 호출 중 오류 발생: {e}")
            target_round -= 1

    return None

def main():
    print("최신 로또 당첨 데이터를 검색합니다...")
    data = get_latest_drawn_round()
    
    if not data:
        print("[Error] 유효한 로또 데이터를 가져오지 못했습니다.")
        return

    draw_no = data["drwNo"]
    
    # GitHub Action 커밋 기록에 맞춘 JSON 구조화
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
        "stores": [], # 1등 배출점 데이터 (별도 크롤링이 없다면 빈 배열 유지)
        "updateTime": datetime.now(pytz.timezone('Asia/Seoul')).strftime("%Y-%m-%d %H:%M:%S (KST)")
    }

    # data 디렉토리가 없으면 생성
    os.makedirs("data", exist_ok=True)
    
    # 1. 개별 회차 파일 저장 (예: data/1225.json)
    filename = f"data/{draw_no}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(formatted_data, f, ensure_ascii=False, indent=2)
    print(f"[Success] {filename} 파일이 성공적으로 생성/업데이트 되었습니다.")

    # 2. (선택사항) 앱에서 항상 최신 정보를 편하게 가져가도록 latest.json도 함께 생성
    latest_filename = "data/latest.json"
    with open(latest_filename, "w", encoding="utf-8") as f:
        json.dump(formatted_data, f, ensure_ascii=False, indent=2)
    print(f"[Success] {latest_filename} 반영 완료.")

if __name__ == "__main__":
    main()
