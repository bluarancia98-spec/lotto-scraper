import requests
import json
import os
from datetime import datetime

def get_latest_draw_no():
    """
    현재 날짜를 기준으로 가장 최신 로또 회차를 계산합니다.
    (동행복권 1회차: 2002년 12월 7일 기준)
    """
    first_draw_date = datetime(2002, 12, 7)
    today = datetime.now()
    days_passed = (today - first_draw_date).days
    latest_draw = (days_passed // 7) + 1
    
    # 토요일(weekday:5) 오후 8시 45분(추첨시간) 이전이거나 일~금요일인 경우 아직 이번주 추첨 전이므로 1을 뺌
    if today.weekday() < 5 or (today.weekday() == 5 and today.hour < 21):
        latest_draw -= 1
        
    return latest_draw

def fetch_lotto_data(draw_no):
    """
    동행복권 공식 API를 사용하여 특정 회차의 당첨 번호를 가져옵니다.
    """
    # 동행복권 공식 API URL
    url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={draw_no}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        # API 호출 성공 여부 확인
        if data.get("returnValue") == "success":
            result = {
                "drawNo": data.get("drwNo"),
                "drawDate": data.get("drwNoDate"),
                "winningNumbers": [
                    data.get("drwtNo1"),
                    data.get("drwtNo2"),
                    data.get("drwtNo3"),
                    data.get("drwtNo4"),
                    data.get("drwtNo5"),
                    data.get("drwtNo6")
                ],
                "bonusNumber": data.get("bnusNo"),
                "firstPrizeAmount": data.get("firstWinamnt"),
                "firstPrizeWinners": data.get("firstPrzwnerCo"),
                "stores": [] # 배출점 정보는 구조가 복잡하여 우선 빈 배열 처리 (앱 에러 방지)
            }
            return result
        else:
            print(f"[오류] {draw_no}회차 데이터를 찾을 수 없습니다. (아직 추첨 전이거나 데이터 없음)")
            return None

    except Exception as e:
        print(f"[오류] 동행복권 서버와 통신 중 예외 발생: {e}")
        return None

def main():
    # 스크린샷 기준 타겟팅 (1226회) 또는 최신 회차 자동 계산
    # target_draw = 1226 # 특정 회차를 고정하려면 주석을 풀고 사용하세요.
    target_draw = get_latest_draw_no() # 자동으로 항상 최신 회차를 찾도록 설정됨

    print(f"[{target_draw}회차] 동행복권 로또 당첨 결과 수집 시작...")
    lotto_data = fetch_lotto_data(target_draw)

    # 데이터 수집에 실패했을 경우에만 앱 크래시 방지용 fallback 데이터 생성
    if lotto_data is None:
        print("데이터를 정상적으로 가져오지 못해 대기 상태의 JSON을 생성합니다.")
        lotto_data = {
            "drawNo": target_draw,
            "drawDate": "발표 대기중 / 통신 지연",
            "winningNumbers": [0, 0, 0, 0, 0, 0],
            "bonusNumber": 0,
            "firstPrizeAmount": 0,
            "firstPrizeWinners": 0,
            "stores": []
        }

    # 루트 디렉토리에 data 폴더 생성
    os.makedirs("data", exist_ok=True)
    file_path = f"data/{target_draw}.json"

    # JSON 파일로 예쁘게 저장
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(lotto_data, f, ensure_ascii=False, indent=2)

    print(f"✅ 데이터 저장 완료: {file_path}")

if __name__ == "__main__":
    main()
