import requests
import sqlite3
from bs4 import BeautifulSoup

DB_NAME = "svetofor_products.db"
def initialize_db():
    """Создаёт таблицу, если её ещё нет."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS svetofor_products (
            category TEXT,
            name TEXT,
            price REAL,
            url TEXT PRIMARY KEY,
            shop TEXT
        )
    """)

    conn.commit()
    conn.close()
    print("База данных готова.")

def save_products(products):
    """
    Сохраняет список товаров в SQLite.
    products — список кортежей (category, name, price, url, shop)
    """
    if not products:
        print("Нет данных для записи.")
        return 0
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        before = conn.total_changes
        cursor.executemany("""
            INSERT OR IGNORE INTO svetofor_products (category, name, price, url, shop)
            VALUES (?, ?, ?, ?, ?)
        """, products)
        conn.commit()
        inserted = conn.total_changes - before
        print(f"Добавлено новых записей: {inserted}")
    except Exception as e:
        print(f"Ошибка SQLite: {e}")
        inserted = 0
    conn.close()
    return inserted

initialize_db()
base_url = "https://svetofornadom.ru"
catalog_url = base_url + "/catalog/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
}

# Шаг 1. Получить категории
response = requests.get(catalog_url, headers=headers)
soup = BeautifulSoup(response.text, "lxml")
categories_block = soup.find('div', class_='section-links__list')
category_links = categories_block.find_all('a', href=True)

for cat in category_links:
    cat_name = cat.get_text(strip=True)
    cat_url = base_url + cat['href']
    print(f"\n--- Категория: {cat_name} ---")
    # Шаг 2. Загрузить страницу категории
    response_cat = requests.get(cat_url, headers=headers)
    soup_cat = BeautifulSoup(response_cat.text, "lxml")
    products_container = soup_cat.find("div", class_="cards__list")
    if not products_container:
        print("Нет товаров в этой категории.")
        continue
    # Шаг 3. Перебрать все карточки товаров
    products_to_save = []
    cards = products_container.find_all("div", class_="card")
    for card in cards:
        title_tag = card.find(class_="card__title")
        price_tag = card.find(class_="card__price")
        name = title_tag.get_text(strip=True) if title_tag else ""
        price = float(price_tag.get_text(strip=True).replace("\xa0", "")[:-5]) if price_tag else ""
        link_tag = card.find("a", href=True)
        url = base_url + link_tag["href"] if link_tag else ""
        products_to_save.append((cat_name, name, price, url, "svetofor"))
        print((cat_name, name, price, url, "svetofor"))
    save_products(products_to_save)

