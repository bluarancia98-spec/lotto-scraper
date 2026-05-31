import requests
import json
import os
from datetime import datetime, timezone, timedelta

def fetch_lotto_data(draw_no):
    """
    동행복권 공식 API를 호출하여 당첨 번호를 가져옵니다.
    """
    url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={draw_no}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("returnValue") == "success":
                return {
                    "drawNo": data.get("drwNo"),
                    "drawDate": data.get("drwNoDate"),
                    "winningNumbers": [
                        data.get("drwtNo1"), data.get("drwtNo2"), data.get("drwtNo3"),
                        data.get("drwtNo4"), data.get("drwtNo5"), data.get("drwtNo6")
                    ],
                    "bonusNumber": data.get("bnusNo"),
                    "firstPrizeAmount": data.get("firstWinamnt"),
                    "firstPrizeWinners": data.get("firstPrzwnerCo"),
                    "stores": []
                }
    except Exception as e:
        print(f"통신 에러 발생: {e}")
        
    return None

def main():
    # 스크린샷 기준, 현재 타겟팅 중인 1226회로 고정
    target_draw = 1226
    print(f"[{target_draw}회차] 동행복권 데이터 수집 시도...")
    
    lotto_data = fetch_lotto_data(target_draw)
    
    # 🌟 깃허브 액션 환경(UTC)을 한국 시간(KST)으로 변환
    kst = timezone(timedelta(hours=9))
    now_kst = datetime.now(kst).strftime("%Y-%m-%d %H:%M:%S")

    # 아직 추첨 전이거나 데이터를 못 가져왔을 때 (0으로 채움)
    if lotto_data is None:
        print("데이터 없음 (미추첨 상태). 앱 오류 방지용 0 데이터를 생성합니다.")
        lotto_data = {
            "drawNo": target_draw,
            "drawDate": "발표 대기중 / 통신 지연",
            "winningNumbers": [0, 0, 0, 0, 0, 0],
            "bonusNumber": 0,
            "firstPrizeAmount": 0,
            "firstPrizeWinners": 0,
            "stores": []
        }
        
    # 🌟 핵심 해결책: 매번 JSON 텍스트 내용이 무조건 바뀌도록 실행 시간을 추가
    # 이렇게 하면 데이터가 0이더라도 시간이 달라지므로 깃허브가 무조건 커밋(업데이트)합니다.
    lotto_data["updateTime"] = f"{now_kst} (KST)"

    # data 폴더 생성 및 JSON 저장
    os.makedirs("data", exist_ok=True)
    file_path = f"data/{target_draw}.json"

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(lotto_data, f, ensure_ascii=False, indent=2)

    print(f"✅ 정상적으로 파일 작성 및 업데이트 완료: {file_path}")

if __name__ == "__main__":
    main()
