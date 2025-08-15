import requests
from bs4 import BeautifulSoup
import time

BOT_TOKEN = "8383543071:AAG_Wlk9HSTHK3Rsn_iLlyJkMieDdE4isBc"
CHAT_ID = "6346457306"
URL = "https://es.kgct.or.kr/es/sim_spot_info?status=2"

last_notice_number = None

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=payload)

def get_latest_notice_number():
    response = requests.get(URL)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    first_row = soup.select_one("table tbody tr td")
    if not first_row:
        return None
    return first_row.get_text(strip=True)

print("공지 확인 시작...")
while True:
    try:
        latest_number = get_latest_notice_number()
        if latest_number is None:
            print("공지 번호를 찾을 수 없습니다.")
        elif last_notice_number is None:
            last_notice_number = latest_number
            print(f"현재 최신 공지 번호: {latest_number}")
        elif latest_number != last_notice_number:
            last_notice_number = latest_number
            message = f"새 공지가 등록되었습니다! (번호: {latest_number})\n{URL}"
            print(message)
            send_telegram_message(message)
        else:
            print(f"새 공지 없음 (최근 번호: {latest_number})")
    except Exception as e:
        print(f"오류 발생: {e}")
    time.sleep(60)
