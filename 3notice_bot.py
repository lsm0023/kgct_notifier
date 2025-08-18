# 3notice_bot.py  (최소 동작 테스트용)
import os
import requests

# GitHub Secrets에서 주입된 환경변수 읽기
BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID   = os.environ["TELEGRAM_CHAT_ID"]

def send_message(text: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text, "disable_web_page_preview": True}
    r = requests.post(url, data=data, timeout=20)
    r.raise_for_status()

def main():
    send_message("✅ GitHub Actions 테스트 알림: 봇이 잘 실행되었습니다!")

if __name__ == "__main__":
    main()