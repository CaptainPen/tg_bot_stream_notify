import os
import time
import requests
from dotenv import load_dotenv
from obswebsocket import obsws, events

# === Загружаем переменные из .env ===
load_dotenv()

# === Telegram ===
# В .env нужно указать:
# TELEGRAM_BOT_TOKEN=твой_токен_бота
# TELEGRAM_CHAT_ID=айди_твоей_группы_или_чата
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# === OBS ===
# В .env нужно указать:
# OBS_HOST=localhost
# OBS_PORT=4455
# OBS_PASSWORD=пароль_websocket_из_OBS
# STREAMERS_NAME=твой_ник_на_twitch
OBS_HOST = os.getenv("OBS_HOST", "localhost")
OBS_PORT = int(os.getenv("OBS_PORT", "4455"))
OBS_PASSWORD = os.getenv("OBS_PASSWORD", "")
STREAMERS_NAME = os.getenv("STREAMERS_NAME", "Dyrka9")

# === Общие настройки ===
# В .env можно указать CHECK_INTERVAL_SECONDS=30
INTERVAL = int(os.getenv("CHECK_INTERVAL_SECONDS", "30"))

# === Telegram: функция отправки сообщений ===
def tg_send_html(text: str):
    """Отправка HTML-сообщений в Telegram"""
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            data={
                "chat_id": CHAT_ID,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": False,
            },
            timeout=10,
        )
        if r.status_code != 200:
            print(f"[TG] Ошибка {r.status_code}: {r.text}")
    except Exception as e:
        print("Ошибка Telegram:", e)

# === OBS ===
stream_was_live = False

def notify_stream_online():
    """Отправка уведомления о начале стрима OBS"""
    global stream_was_live
    if stream_was_live:
        return
    stream_was_live = True

    stream_url = f"https://www.twitch.tv/{STREAMERS_NAME}"
    stream_msg = f"""
💙 <b>Прямая трансляция на Twitch!</b>  
📺 Стример: {STREAMERS_NAME}

🔥 Присоединяйся и смотри прямо здесь 👇  
<a href="{stream_url}">Смотреть на Twitch</a>
"""
    tg_send_html(stream_msg.strip())

def notify_stream_offline():
    """Отправка уведомления о завершении стрима"""
    global stream_was_live
    if not stream_was_live:
        return
    stream_was_live = False

    msg = """
🔴 <b>Стрим завершён</b>  
🕹️ Спасибо, что были с нами 💫  
💬 Поддержи стримера и не пропусти следующий эфир!  
📅 Следи за обновлениями — скоро снова в эфире 💥
"""
    tg_send_html(msg.strip())

def on_any_event(message):
    """Обрабатывает события OBS о трансляции"""
    try:
        data = message.__dict__
        if data.get("name") != "StreamStateChanged":
            return

        payload = data.get("datain", {})
        state = payload.get("outputState")
        active = payload.get("outputActive")

        if active and state == "OBS_WEBSOCKET_OUTPUT_STARTED":
            notify_stream_online()
        elif not active and state == "OBS_WEBSOCKET_OUTPUT_STOPPED":
            notify_stream_offline()
    except Exception as e:
        print("Ошибка OBS:", e)

def connect_obs():
    """Подключается к OBS WebSocket и слушает события"""
    while True:
        try:
            print(f"🔌 Подключаюсь к OBS WebSocket ({OBS_HOST}:{OBS_PORT})...")
            ws = obsws(OBS_HOST, OBS_PORT, OBS_PASSWORD)
            ws.connect()
            print("✅ Подключено к OBS WebSocket.")

            ws.register(on_any_event)
            ws.register(on_any_event, events.StreamStarted)
            ws.register(on_any_event, events.StreamStopped)

            while True:
                time.sleep(1)
        except Exception as e:
            print("❌ Ошибка OBS:", e)
            print("🔁 Повторное подключение через 5 сек...")
            time.sleep(5)

# === Запуск ===
if __name__ == "__main__":
    print("🚀 Dyrka9-бот запущен: оповещения отслеживаются.")
    connect_obs()
