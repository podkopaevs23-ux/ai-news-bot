#!/usr/bin/env python3
"""
Версия для cron (запускается раз в день)
Используйте с: python bot_cron.py
"""
import os
from news_smart import collect_agent_news, create_agent_summary, send_telegram

# Подхватываем переменные окружения
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8216975392:AAFZfo-2Pa8NX43Pev70t_8DiZ5ym92aOJI")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "929964431")

def main():
    print("="*50)
    print("🚀 Запуск сбора новостей...")
    print("="*50)
    
    news = collect_agent_news()
    
    if not news:
        print("Нет новостей")
        return
    
    summary = create_agent_summary(news)
    
    if send_telegram(summary):
        print(f"✅ Отправлено {len(news)} новостей!")
    else:
        print("Ошибка отправки")
    
    print("="*50)

if __name__ == "__main__":
    main()