# 3notice_bot.py  (KGCT 공지 모니터링: 원샷 실행)
import os, json, re, sys, requests
from bs4 import BeautifulSoup

BOT_TOKEN  = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID    = os.environ["TELEGRAM_CHAT_ID"]

TARGET_URL = "https://es.kgct.or.kr/es/sim_spot_info?status=2"
STATE_FILE = "state.json"   # 워크플로가 변경 시 커밋하도록 설정되어 있음
DEBUG      = os.getenv("DEBUG") == "1"
BOOTSTRAP  = os.getenv("BOOTSTRAP_ON_START") == "1"

LABELS = ["번호","교육시설유형","소재지역","교육기관명","공고명","심사참여신청기간","심사일(시)","조회수"]

def send_message(text: str, html: bool=True):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text, "disable_web_page_preview": True}
    if html: data["parse_mode"] = "HTML"
    r = requests.post(url, data=data, timeout=20)
    r.raise_for_status()

def norm_header(t: str) -> str:
    t = re.sub(r"\s+","", (t or "").strip())
    m = {
        "번호":"번호", "교육시설유형":"교육시설유형", "교육시설 유형":"교육시설유형",
        "소재지역":"소재지역","지역":"소재지역","교육기관명":"교육기관명","기관명":"교육기관명",
        "공고명":"공고명","제목":"공고명","심사참여신청기간":"심사참여신청기간","신청기간":"심사참여신청기간",
        "심사일(시)":"심사일(시)","심사일":"심사일(시)","조회수":"조회수"
    }
    return m.get(t, t)

def clean(s: str) -> str:
    return re.sub(r"\s+"," ", (s or "").strip())

def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_state(s: dict):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=2)

def fetch_latest():
    r = requests.get(TARGET_URL, timeout=30, headers={"User-Agent":"Mozilla/5.0"})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    table = soup.select_one("table")
    if not table:
        if DEBUG: print("[DEBUG] table not found"); 
        return None

    # 헤더 매핑
    header_map = {}
    thead = table.select_one("thead tr")
    header_cells = thead.find_all(["th","td"]) if thead else None
    if not header_cells:
        first = table.select_one("tbody tr")
        if first and first.find_all("th"): header_cells = first.find_all(["th","td"])
    if header_cells:
        for i,h in enumerate(header_cells):
            header_map[norm_header(h.get_text(strip=True))] = i

    # 본문 첫 행(최신)
    body_rows = table.select("tbody tr")
    if not body_rows:
        trs = table.select("tr")
        body_rows = trs[1:] if len(trs)>1 else []
    if not body_rows: return None
    row = body_rows[0]
    if row.find_all("th") and len(body_rows)>1:
        row = body_rows[1]
    cells = row.find_all("td") or row.find_all("th")
    if not cells: return None

    # 헤더가 없어도 동작하도록 폴백 인덱스
    fallbacks = {"번호":0,"교육시설유형":1,"소재지역":2,"교육기관명":3,"공고명":4,"심사참여신청기간":5,"심사일(시)":6,"조회수":7}

    def v(label):
        idx = header_map.get(label, fallbacks.get(label))
        if idx is None or idx>=len(cells): return ""
        if label=="공고명":
            a = cells[idx].select_one("a")
            return clean(a.get_text(strip=True) if a else cells[idx].get_text(" ",strip=True))
        return clean(cells[idx].get_text(" ",strip=True))

    data = {lab: v(lab) for lab in LABELS}

    # 상세 링크
    title_idx = header_map.get("공고명", fallbacks["공고명"])
    href = ""
    if title_idx is not None and title_idx < len(cells):
        a = cells[title_idx].select_one("a")
        if a and a.has_attr("href"):
            href = a["href"]
    full = href if (href and href.startswith("http")) else (f"https://es.kgct.or.kr{href}" if href else TARGET_URL)

    key = f"{data.get('공고명','')}|{full}"

    # 전송 메시지 만들기
    lines = ["🆕 <b>새 공지</b>"]
    for lab in LABELS:
        if data.get(lab):
            lines.append(f"<b>{lab}</b>: {data[lab]}")
    lines.append(f'<a href="{full}">상세 보기</a>')
    return {"key": key, "message": "\n".join(lines)}

def main():
    state = load_state()
    last_key = state.get("last_key")

    item = fetch_latest()
    if not item:
        if DEBUG: print("[DEBUG] no item parsed")
        return 0

    # 처음 한 번 강제 발송하고 시작하려면 BOOTSTRAP_ON_START=1 사용
    if BOOTSTRAP and last_key is None:
        send_message(item["message"], html=True)
        save_state({"last_key": item["key"]})
        if DEBUG: print("[BOOTSTRAP] sent first item")
        return 0

    if item["key"] != last_key:
        send_message(item["message"], html=True)
        save_state({"last_key": item["key"]})
        if DEBUG: print("[DEBUG] NEW -> sent")
    else:
        if DEBUG: print("[DEBUG] no change")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print("[ERROR]", repr(e))
        sys.exit(1)
