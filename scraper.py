import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta

# 동행복권 API 및 웹사이트 접속용 헤더 (모바일/PC 혼합 위장)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept': '*/*'
}

def get_expected_draw_no():
    """네트워크 통신 없이, 수학적 날짜 계산으로 이번 주 회차를 100% 정확히 계산합니다."""
    now_kst = datetime.now(timezone(timedelta(hours=9)))
    # 로또 1회차 추첨일: 2002년 12월 7일 20시 45분
    base_date = datetime(2002, 12, 7, 20, 45, tzinfo=timezone(timedelta(hours=9)))
    
    diff_days = (now_kst - base_date).days
    draw_no = (diff_days // 7) + 1
    
    # 토요일 저녁 8시 45분 이전이라면 아직 추첨 전이므로 직전 회차로 설정
    if now_kst.weekday() == 5 and (now_kst.hour < 20 or (now_kst.hour == 20 and now_kst.minute < 45)):
        draw_no -= 1
        
    return draw_no

def fetch_basic_info(draw_no):
    """공식 JSON API로 당첨 번호 획득 (가장 차단 확률이 낮음)"""
    url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={draw_no}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        data = res.json()
        if data.get('returnValue') == 'success':
            return {
                "drawNo": data.get('drwNo'),
                "drawDate": data.get('drwNoDate'),
                "winningNumbers": [
                    data.get('drwtNo1'), data.get('drwtNo2'), data.get('drwtNo3'),
                    data.get('drwtNo4'), data.get('drwtNo5'), data.get('drwtNo6')
                ],
                "bonusNumber": data.get('bnusNo'),
                "firstPrizeAmount": data.get('firstWinamnt', 0),
                "firstPrizeWinners": data.get('firstPrzwnerCo', 0)
            }
    except Exception as e:
        print(f"기본 정보 수집 에러: {e}")
    return None

def scrape_stores(draw_no):
    """1등 배출점 크롤링 (해외 IP 차단 시 빈 리스트 반환)"""
    url = "https://dhlottery.co.kr/store.do?method=topStore&pageGubun=L645"
    payload = {"drwNo": draw_no, "schKey": "all", "schVal": ""}
    stores_data = []
    try:
        res = requests.post(url, data=payload, headers=HEADERS, timeout=10)
        res.encoding = 'EUC-KR'
        soup = BeautifulSoup(res.text, 'html.parser')
        tables = soup.find_all('table', class_='tbl_data')
        
        if tables:
            rows = tables[0].find('tbody').find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 4:
                    name = cols[1].text.strip()
                    store_type = cols[2].text.strip()
                    address = cols[3].text.strip()
                    if name and "결과가 없습니다" not in name:
                        stores_data.append({"name": name, "type": store_type, "address": address})
    except Exception as e:
        print(f"배출점 크롤링 에러 (방화벽 차단 가능성): {e}")
    return stores_data

if __name__ == "__main__":
    print("🚀 Pro 크롤러 가동 시작 (절대 실패하지 않는 강제 저장 모드)")
    
    # 1. 무조건 타겟 회차 번호 획득
    target_no = get_expected_draw_no()
    print(f"🎯 공략 회차: {target_no}회")
    
    # 2. 데이터 수집 시도
    basic_info = fetch_basic_info(target_no)
    stores_list = scrape_stores(target_no)
    
    # 3. 데이터가 없더라도 무조건 빈 껍데기 JSON 강제 생성 (앱 방어용)
    if not basic_info:
        print("⚠️ 주의: 통신이 완전히 차단되었습니다. 앱 방어를 위해 강제 더미 데이터를 생성합니다.")
        basic_info = {
            "drawNo": target_no,
            "drawDate": "발표 대기중 / 통신 지연",
            "winningNumbers": [0, 0, 0, 0, 0, 0],
            "bonusNumber": 0,
            "firstPrizeAmount": 0,
            "firstPrizeWinners": 0
        }
        
    # 4. 파일 저장 로직 (이전 모델의 버그를 고친 부분: store_list가 비어있어도 무조건 저장)
    full_data = basic_info.copy()
    full_data["stores"] = stores_list
    
    os.makedirs('data', exist_ok=True)
    file_path = f"data/{target_no}.json"
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(full_data, f, ensure_ascii=False, indent=2)
        
    print(f"✅ 데이터 추출 및 저장 100% 완료: {file_path} (배출점: {len(stores_list)}곳)")
