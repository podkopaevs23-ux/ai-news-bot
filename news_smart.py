import requests
import re
from datetime import datetime
from typing import List, Dict
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, SEND_HOUR, SEND_MINUTE
import time

# Источники — Google News и крупные издания
SOURCES = {
    "Google RU 1": "https://news.google.com/rss/search?q=нейросети+агент+автоматизация&hl=ru&gl=RU&ceid=RU:ru",
    "Google RU 2": "https://news.google.com/rss/search?q=искусственный+интеллект+робот&hl=ru&gl=RU&ceid=RU:ru",
    "Google RU 3": "https://news.google.com/rss/search?q=AI+агент+робот+замена+людей&hl=ru&gl=RU&ceid=RU:ru",
    "Google EN 1": "https://news.google.com/rss/search?q=AI+agent+replace+human&hl=en-US&gl=US&ceid=US:en",
    "Google EN 2": "https://news.google.com/rss/search?q=autonomous+AI+agent&hl=en-US&gl=US&ceid=US:en",
    "Google EN 3": "https://news.google.com/rss/search?q=AI+agent+tool+launch&hl=en-US&gl=US&ceid=US:en",
    "TechCrunch": "https://techcrunch.com/feed/",
    "MIT Tech Review": "https://www.technologyreview.com/feed/",
}

# Ключевые слова для AI-агентов
AGENT_KEYWORDS = [
    "агент", "agent", "автоматизация", "автономный", "autonomous",
    "заменит", "замена", "робот", "бот", "нейросеть", "искусственный интеллект",
    "автоматизировать", "automation", "replace", "решение задач",
    "бот", "chatbot", "голосовой", "цифровой помощник",
    "ai agent", "virtual agent", "software agent",
]

NOISE = ["закон", "суд", "скандал", "акции", "прогноз"]


def fix_link(link: str) -> str:
    """Исправляет ссылки для корректного открытия"""
    # Убираем редиректы Google
    if "news.google.com" in link:
        # Извлекаем оригинальный URL из редиректа
        if "url=" in link:
            match = re.search(r'url=([^&]+)', link)
            if match:
                import urllib.parse
                link = urllib.parse.unquote(match.group(1))
        # Меняем /read-aloud/ и другие форматы на /articles/
        link = re.sub(r'/read-aloud/.*$', '', link)
        if "news.google.com" in link and "/articles/" not in link and "search?" not in link:
            # Это ссылка на статью без /articles/, добавляем
            link = link.replace("?outputType=amp", "").replace("?ns=1", "")
    
    # Убираем параметры, которые могут мешать
    link = link.split("&")[0] if "&" in link else link
    link = link.split("?")[0] if "?" in link and "/articles/" not in link else link
    
    return link.strip()


def is_agent_news(title: str, description: str) -> bool:
    text = (title + " " + description).lower()
    for word in NOISE:
        if word in text:
            return False
    matches = sum(1 for kw in AGENT_KEYWORDS if kw.lower() in text)
    return matches >= 1


def fetch_rss(url: str) -> List[Dict]:
    news = []
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/rss+xml, application/xml, text/xml, */*"
        }
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        content = response.text
        
        items = re.findall(r'<item>(.*?)</item>', content, re.DOTALL)
        
        for item in items[:40]:
            # Ищем заголовок
            title_match = re.search(r'<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>', item, re.DOTALL)
            # Ищем ссылку — несколько вариантов формата
            link_match = re.search(r'<link>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</link>', item, re.DOTALL)
            # Ищем описание
            desc_match = re.search(r'<description>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</description>', item, re.DOTALL)
            # Ищем оригинальную ссылку (для Google News)
            orig_link_match = re.search(r'<origLink>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</origLink>', item, re.DOTALL)
            
            title = (title_match.group(1) or "").strip() if title_match else ""
            # Приоритет: origLink > link
            link = ""
            if orig_link_match:
                link = orig_link_match.group(1).strip()
            elif link_match:
                link = link_match.group(1).strip()
            desc = (desc_match.group(1) or "").strip() if desc_match else ""
            
            if title and link:
                # Фиксим ссылку
                link = fix_link(link)
                
                # Очищаем описание
                desc = re.sub(r'<[^>]+>', '', desc)
                desc = re.sub(r'\s+', ' ', desc).strip()[:400]
                
                news.append({
                    "title": title,
                    "link": link,
                    "description": desc,
                    "source": url.split("/")[2] if "/" in url else url
                })
                
    except Exception as e:
        print(f"  Ошибка: {e}")
    
    return news


def collect_agent_news() -> List[Dict]:
    print("Поиск новостей про AI-агентов...")
    all_news = []
    
    for source, url in SOURCES.items():
        print(f"  {source}...", end=" ", flush=True)
        news = fetch_rss(url)
        print(f"{len(news)} найдено")
        all_news.extend(news)
        time.sleep(0.5)
    
    # Фильтруем
    agents = [n for n in all_news if is_agent_news(n["title"], n["description"])]
    
    # Убираем дубликаты
    seen = set()
    unique = []
    for item in agents:
        if item["title"] not in seen:
            seen.add(item["title"])
            unique.append(item)
    
    print(f"Новостей про AI-агентов: {len(unique)} из {len(all_news)}")
    return unique


def create_agent_summary(news: List[Dict]) -> str:
    today = datetime.now().strftime("%d.%m.%Y")
    
    message = f"🤖 Ежедневный дайджест | {today}\n"
    message += "━━━━━━━━━━━━━━━━━━━━━━━\n"
    message += "Тема: AI-агенты и автоматизация\n"
    message += f"Найдено свежих новостей: {len(news)}\n\n"
    
    if not news:
        message += "Сегодня нет свежих новостей.\n"
        return message
    
    # Все новости (Telegram允許 до 4096 символов)
    for i, item in enumerate(news, 1):
        title = item["title"][:120] + "..." if len(item["title"]) > 120 else item["title"]
        desc = item["description"][:100] if item["description"] else ""
        
        message += f"{i}. {title}\n"
        
        if desc:
            message += f"   {desc}\n"
        
        message += f"   Ссылка: {item['link']}\n\n"
    
    message += "━━━━━━━━━━━━━━━━━━━━━━━\n"
    message += "Авторассылка | Каждый день в 18:00"
    
    return message


def send_telegram(text: str) -> bool:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    # Разбиваем если слишком длинно
    if len(text) > 4096:
        parts = []
        current = ""
        for line in text.split("\n"):
            if len(current) + len(line) + 1 > 4000:
                if current:
                    parts.append(current)
                current = line
            else:
                current += "\n" + line
        if current:
            parts.append(current)
        
        success = True
        for part in parts:
            data = {"chat_id": TELEGRAM_CHAT_ID, "text": part}
            try:
                response = requests.post(url, json=data, timeout=30)
                if not response.json().get("ok"):
                    success = False
            except:
                success = False
            time.sleep(1)  # Не спамить
        return success
    else:
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
        try:
            response = requests.post(url, json=data, timeout=30)
            return response.json().get("ok", False)
        except:
            return False


def daily_send():
    print("\n" + "="*50)
    print("Запуск рассылки про AI-агентов...")
    
    news = collect_agent_news()
    
    if not news:
        print("Нет новостей")
        return
    
    summary = create_agent_summary(news)
    
    if send_telegram(summary):
        print("Отправлено!")
    else:
        print("Ошибка отправки")
    
    print("="*50)


if __name__ == "__main__":
    daily_send()