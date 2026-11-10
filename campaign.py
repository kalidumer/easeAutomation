
import os
import json
import sqlite3
import urllib.request
import urllib.parse
import logging
from datetime import datetime, timezone

BOT_TOKEN = os.environ["BOT_TOKEN"]
API = f"https://api.telegram.org/bot{BOT_TOKEN}/"

MAX_TARGETS_PER_RUN = 10
DATABASE = "campaign.db"

MESSAGE = """🎓 EASE ONLINE ACADEMY 🇪🇹

Discover Ease Online Academy, an educational platform designed to help students access learning resources and improve their knowledge via tutoring themselves.

🌐 https://ease-online-academy.ai.studio

Ease Online Academy ለተማሪዎች የትምህርት መረጃዎችንና የመማሪያ ግብዓቶችን ለማግኘት የሚረዳ የትምህርት መድረክ ነው። እንዲሁም እራሳቸው ማጥናት ሚችሉበት መንገድ አመቻችቶ መጥቷል!

🌐 https://ease-online-academy.ai.studio

Ease Online Academy waltajjii barnootaa barattoonni beekumsa isaanii guddisuu fi meeshaalee barnootaa argachuuf itti fayyadamuu danda'aniidha.

🌐 https://ease-online-academy.ai.studio

❤️ Share with Ethiopian students!
Education creates opportunities.
"""

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

def database():
    conn = sqlite3.connect(DATABASE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sent (
            chat_id TEXT NOT NULL,
            sent_date TEXT NOT NULL,
            PRIMARY KEY(chat_id, sent_date)
        )
    """)
    conn.commit()
    return conn

def load_targets():
    with open("targets.txt", encoding="utf-8") as f:
        return list(dict.fromkeys(
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#")
        ))

def telegram_send(chat_id):
    payload = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": MESSAGE,
        "disable_web_page_preview": "false"
    }).encode()

    request = urllib.request.Request(
        API + "sendMessage",
        data=payload,
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.loads(response.read().decode())

    if not result.get("ok"):
        raise RuntimeError(result.get("description", "Send failed"))

    return result

def run_campaign():
    today = datetime.now(timezone.utc).date().isoformat()

    conn = database()
    targets = load_targets()

    sent_count = 0

    logging.info("Starting Ease Online Academy campaign")

    for chat_id in targets:

        if sent_count >= MAX_TARGETS_PER_RUN:
            break

        previous = conn.execute(
            "SELECT 1 FROM sent WHERE chat_id=? AND sent_date=?",
            (chat_id, today)
        ).fetchone()

        if previous:
            continue

        try:
            telegram_send(chat_id)

            conn.execute(
                "INSERT INTO sent VALUES (?, ?)",
                (chat_id, today)
            )
            conn.commit()

            sent_count += 1
            logging.info("Delivered successfully: %s", chat_id)

        except Exception as error:
            logging.error("Failed for %s: %s", chat_id, error)

    logging.info("Campaign finished: %s successful posts", sent_count)
    conn.close()

if __name__ == "__main__":
    run_campaign()
