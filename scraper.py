import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# 💡 [핵심] 깃허브 로봇이 아닌, 한국의 윈도우 크롬 사용자처럼 완벽하게 위장하는 헤더
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    'Referer': 'https://dhlottery.co.kr/',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

def get_latest_draw_no(session):
    """메인 페이지를 우회 접속하여 최신 회차를 추출합니다."""
    try:
        url = "https://dhlottery.co.kr/common.do?method=main"
        response = session.get(url, headers=HEADERS, timeout=15)
        response.encoding = 'EUC-KR'
        soup = BeautifulSoup(response.text, 'html.parser')
        draw_no_tag = soup.find('strong', id='lottoDrwNo')
        if draw_no_tag:
            return int(draw_no_tag.text.strip())
    except Exception as e:
        print(f"회차 추출 에러: {e}")
        
    # 만약 HTML 파싱에 실패했다면, API를 통해 확실하게 한 번 더 검증
    try:
        now_kst = datetime.utcnow() + timedelta(hours=9)
        base_date = datetime(2002, 12, 7, 20, 45)
        draw_no = (now_kst - base_date).days // 7 + 1
        if now_kst.weekday() == 5 and (now_kst.hour < 20 or (now_kst.hour == 20 and now_kst.minute < 45)):
            draw_no -= 1
            
        url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={draw_no}"
        res = session.get(url, headers=HEADERS, timeout=10)
        if res.json().get('returnValue') == 'success':
            return draw_no
    except Exception as e:
        print(f"API 검증 에러: {e}")
    return None

def fetch_basic_info(session, draw_no):
    """당첨 번호 및 금액 정보 획득"""
    try:
        url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={draw_no}"
        response = session.get(url, headers=HEADERS, timeout=15)
        if response.status_code == 200:
            data = response.json()
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
        print(f"기본 정보 수집 실패: {e}")
    return None

def scrape_stores(session, draw_no):
    """1등 배출점 목록 크롤링 (차단 우회)"""
    url = "https://dhlottery.co.kr/store.do?method=topStore&pageGubun=L645"
    payload = {"drwNo": draw_no, "schKey": "all", "schVal": ""}
    
    try:
        response = session.post(url, data=payload, headers=HEADERS, timeout=15)
        response.encoding = 'EUC-KR'
        soup = BeautifulSoup(response.text, 'html.parser')
        stores_data = []
        
        tables = soup.find_all('table', class_='tbl_data')
        if not tables:
            print("테이블 획득 실패. 구조 변경 또는 우회 실패.")
            return []
            
        rows = tables[0].find('tbody').find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 4:
                name = cols[1].text.strip()
                store_type = cols[2].text.strip()
                address = cols[3].text.strip()
                
                if name and "결과가 없습니다" not in name:
                    stores_data.append({
                        "name": name,
                        "type": store_type,
                        "address": address
                    })
        return stores_data
    except Exception as e:
        print(f"배출점 크롤링 실패: {e}")
        return []

if __name__ == "__main__":
    print("🚀 완벽 위장 크롤러 구동 시작...")
    
    # 💡 [핵심] requests.Session()을 사용해 진짜 브라우저처럼 쿠키를 유지하며 접속
    session = requests.Session()
    
    latest_no = get_latest_draw_no(session)
    if latest_no:
        print(f"🎯 공략 회차: {latest_no}회")
        
        basic_info = fetch_basic_info(session, latest_no)
        stores_list = scrape_stores(session, latest_no)
        
        if basic_info and stores_list:
            full_data = basic_info.copy()
            full_data["stores"] = stores_list
            
            os.makedirs('data', exist_ok=True)
            file_path = f"data/{latest_no}.json"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(full_data, f, ensure_ascii=False, indent=2)
                
            print(f"✅ 방화벽 우회 성공! 데이터 추출 및 저장 완료: {file_path} (배출점: {len(stores_list)}곳)")
        else:
            print("❌ 데이터 추출에 실패했습니다. (차단되었거나 데이터가 발표되지 않음)")
    else:
        print("❌ 회차 번호를 파악할 수 없습니다.")
