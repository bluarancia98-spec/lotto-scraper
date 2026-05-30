import os
import json
import requests
from bs4 import BeautifulSoup

def get_latest_draw_no():
    """동행복권 메인 페이지에서 가장 최근 회차 번호를 알아냅니다."""
    try:
        url = "https://dhlottery.co.kr/common.do?method=main"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        draw_no_tag = soup.find('strong', id='lottoDrwNo')
        if draw_no_tag:
            return int(draw_no_tag.text.strip())
    except Exception as e:
        print(f"회차 추출 실패: {e}")
    return None

def fetch_basic_info(draw_no):
    """공식 API를 통해 당첨 번호, 날짜, 당첨금 정보를 가져옵니다."""
    try:
        url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={draw_no}"
        response = requests.get(url, timeout=15)
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
        print(f"기본 당첨 정보 추출 실패: {e}")
    return None

def scrape_stores(draw_no):
    """PC 버전 배출점 페이지에서 1등 당첨점 목록을 긁어옵니다."""
    url = "https://dhlottery.co.kr/store.do?method=topStore&pageGubun=L645"
    data = {"drwNo": draw_no, "schKey": "all", "schVal": ""}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        response = requests.post(url, data=data, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        stores_data = []
        
        tables = soup.find_all('table', class_='tbl_data')
        if not tables:
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
        print(f"배출점 수집 실패: {e}")
        return []

if __name__ == "__main__":
    latest_no = get_latest_draw_no()
    if latest_no:
        print(f"발견된 최신 회차: {latest_no}회")
        
        basic_info = fetch_basic_info(latest_no)
        stores_list = scrape_stores(latest_no)
        
        if basic_info:
            # 흩어져 있던 정보를 하나의 JSON으로 완벽하게 결합
            full_data = basic_info.copy()
            full_data["stores"] = stores_list
            
            os.makedirs('data', exist_ok=True)
            file_path = f"data/{latest_no}.json"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(full_data, f, ensure_ascii=False, indent=2)
            print(f"성공: {file_path} 파일 생성 완료 (당첨점 {len(stores_list)}곳 포함)")
        else:
            print("기본 당첨 정보를 가져오지 못해 저장하지 않았습니다.")
