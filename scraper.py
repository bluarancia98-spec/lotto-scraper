import os
import json
import requests
from bs4 import BeautifulSoup

def get_latest_draw_no():
    """동행복권 메인 페이지에서 최신 회차를 추출합니다."""
    try:
        url = "https://www.dhlottery.co.kr/common.do?method=main"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'EUC-KR'
        soup = BeautifulSoup(response.text, 'html.parser')
        draw_no_tag = soup.find('strong', id='lottoDrwNo')
        if draw_no_tag:
            return int(draw_no_tag.text.strip())
    except Exception as e:
        print(f"회차 추출 실패: {e}")
    return None

def fetch_basic_info(draw_no):
    """당첨 번호와 금액 정보를 추출합니다."""
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
        print(f"기본 정보 추출 실패: {e}")
    return None

def scrape_stores(draw_no):
    """1등 배출점 목록을 추출합니다."""
    url = "https://www.dhlottery.co.kr/store.do?method=topStore&pageGubun=L645"
    data = {"drwNo": draw_no, "schKey": "all", "schVal": ""}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        response = requests.post(url, data=data, headers=headers, timeout=15)
        response.encoding = 'EUC-KR'
        soup = BeautifulSoup(response.text, 'html.parser')
        stores_data = []
        
        tables = soup.find_all('table', class_='tbl_data')
        if not tables:
            print("테이블을 찾을 수 없습니다.")
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
        print(f"배출점 추출 실패: {e}")
        return []

if __name__ == "__main__":
    # 💡 기획자님이 GitHub Secrets에 넣은 구글 맵 API 키를 파이썬에서 불러옵니다. (다음 단계 위치 변환용)
    google_maps_api_key = os.environ.get("MAPS_API_KEY", "")
    if google_maps_api_key:
        print("✅ 구글 맵 API 키가 성공적으로 연결되었습니다.")
    else:
        print("⚠️ 구글 맵 API 키가 없습니다. 데이터 추출만 진행합니다.")

    latest_no = get_latest_draw_no()
    
    if latest_no:
        print(f"진행 회차: {latest_no}회")
        basic_info = fetch_basic_info(latest_no)
        stores_list = scrape_stores(latest_no)
        
        # 기본 정보가 없더라도 기본 골격은 만듭니다. (에러 방지)
        full_data = basic_info.copy() if basic_info else {
            "drawNo": latest_no,
            "drawDate": "",
            "winningNumbers": [],
            "bonusNumber": 0,
            "firstPrizeAmount": 0,
            "firstPrizeWinners": 0
        }
        full_data["stores"] = stores_list
        
        # 💡 [핵심] 실패하더라도 폴더와 파일은 무조건 만들도록 강제합니다.
        os.makedirs('data', exist_ok=True)
        file_path = f"data/{latest_no}.json"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(full_data, f, ensure_ascii=False, indent=2)
        print(f"✅ 완료: {file_path} 파일 강제 저장 성공 (배출점 {len(stores_list)}곳)")
