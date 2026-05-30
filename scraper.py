import os
import json
import requests
from bs4 import BeautifulSoup

def get_latest_draw_no():
    # 동행복권 공식 결과 페이지에서 가장 최근 회차 번호를 알아냅니다.
    try:
        url = "https://m.dhlottery.co.kr/gameResult.do?method=byWin"
        response = requests.get(url, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        draw_text = soup.find('h3', class_='tit').text
        draw_no = int(''.join(filter(str.isdigit, draw_text)))
        return draw_no
    except Exception as e:
        print(f"회차 추출 실패: {e}")
        return None

def scrape_stores(draw_no):
    # 해당 회차의 1등 당첨점 목록을 모바일 페이지에서 긁어옵니다.
    url = f"https://m.dhlottery.co.kr/gameResult.do?method=byWin&drwNo={draw_no}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G965N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'
    }
    
    response = requests.get(url, headers=headers, timeout=15)
    if response.status_code != 200:
        print("동행복권 서버에 접근할 수 없습니다.")
        return
        
    soup = BeautifulSoup(response.text, 'html.parser')
    stores_data = []
    
    # 1등 당첨점 표 찾기
    table = soup.find('table', {'summary': '1등 배출점 매장명, 구분, 주소 제공'})
    if not table:
        print(f"{draw_no}회 배출점 데이터가 아직 업데이트되지 않았습니다.")
        return
        
    rows = table.find('tbody').find_all('tr')
    for row in rows:
        cols = row.find_all('td')
        if len(cols) >= 3:
            name = cols[0].text.strip()
            store_type = cols[1].text.strip()
            address = cols[2].text.strip()
            
            stores_data.append({
                "name": name,
                "type": store_type,
                "address": address
            })
            
    # 수집한 데이터를 data 폴더 안에 '회차.json' 파일로 저장합니다.
    os.makedirs('data', exist_ok=True)
    file_path = f"data/{draw_no}.json"
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(stores_data, f, ensure_ascii=False, indent=2)
    print(f"성공: {file_path} 파일이 성공적으로 만들어졌습니다. (총 {len(stores_data)}곳)")

if __name__ == "__main__":
    latest_no = get_latest_draw_no()
    if latest_no:
        print(f"발견된 최신 회차: {latest_no}회")
        scrape_stores(latest_no)
