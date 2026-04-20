import requests
import time
import logging
from datetime import datetime, timedelta
from news_smart import collect_agent_news, create_agent_summary, send_telegram
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, SEND_HOUR, SEND_MINUTE

# Настройка логов
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def wait_until_scheduled_time():
    """Ждёт до следующего запланированного времени"""
    now = datetime.now()
    scheduled_today = now.replace(hour=SEND_HOUR, minute=SEND_MINUTE, second=0, microsecond=0)
    
    if now >= scheduled_today:
        next_run = scheduled_today + timedelta(days=1)
    else:
        next_run = scheduled_today
    
    return next_run


def daily_news_job():
    """Ежедневная отправка про AI-агентов"""
    logger.info("="*50)
    logger.info("🚀 Запуск сбора новостей про AI-агентов...")
    
    try:
        news = collect_agent_news()
        
        if not news:
            logger.warning("Нет новостей про AI-агентов")
            return
        
        summary = create_agent_summary(news)
        
        if send_telegram(summary):
            logger.info(f"✅ Отправлено {len(news)} новостей в Telegram!")
        else:
            logger.error("Ошибка отправки в Telegram")
            
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
    
    logger.info("="*50)


def test_send():
    """Тестовая отправка"""
    logger.info("🧪 Тестовая отправка про AI-агентов...")
    daily_news_job()


def main():
    logger.info("🤖 Бот AI-Agents Дайджест запущен!")
    logger.info(f"📅 Расписание: каждый день в {SEND_HOUR:02d}:{SEND_MINUTE:02d}")
    logger.info("🎯 Тема: AI-агенты и замена человека")
    logger.info("📡 Источники: Google News + Tech-издания")
    
    while True:
        next_run = wait_until_scheduled_time()
        now = datetime.now()
        seconds_until_run = (next_run - now).total_seconds()
        
        logger.info(f"⏳ Следующая отправка: {next_run.strftime('%d.%m.%Y %H:%M:%S')}")
        
        while seconds_until_run > 60:
            time.sleep(60)
            now = datetime.now()
            seconds_until_run = (next_run - now).total_seconds()
        
        while seconds_until_run > 0:
            time.sleep(1)
            now = datetime.now()
            seconds_until_run = (next_run - now).total_seconds()
        
        daily_news_job()


if __name__ == "__main__":
    main()