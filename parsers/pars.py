from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import sqlite3
import random
import sys
import os
sys.setrecursionlimit(2000)

DB_NAME = 'okey_products.db'

print("путь к базе данных:", os.path.abspath(DB_NAME))

def initialize_db():
    """создает базу данных и таблицу для продуктов"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS okey_products (
            category TEXT,
            name TEXT,
            price REAL,
            url TEXT PRIMARY KEY,
            shop TEXT
        )
    ''')

    conn.commit()
    conn.close()
    print(f"база данных '{DB_NAME}' и таблица 'okey_products' готовы")


def create_stealth_driver():
    """создает настроенный chrome webdriver"""
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver


def get_category_links(driver):
    """находит ссылки на категории на текущей странице"""
    category_links = []
    category_blocks = driver.find_elements(By.CLASS_NAME, "col-xs-5")

    for cat_block in category_blocks:
        try:
            link = cat_block.find_element(By.CSS_SELECTOR, "h2 a")
            category_links.append((link.text.strip(), link.get_attribute("href")))
        except:
            continue

    return category_links


def parse_products_on_page(driver, category_name):
    """парсит товары на странице и записывает в БД"""

    all_li = driver.find_elements(By.CSS_SELECTOR, ".grid_mode li")
    valid_products = []

    for li in all_li:
        try:
            li.find_element(By.CSS_SELECTOR, ".product-name a")
            valid_products.append(li)
        except:
            continue

    print(f"    найдено товаров: {len(valid_products)}")

    if not valid_products:
        return False

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    products_to_insert = []

    for j, product in enumerate(valid_products):
        try:
            name_link = product.find_element(By.CSS_SELECTOR, ".product-name a")
            name = name_link.text.strip()
            product_url = name_link.get_attribute("href")

            price_input_element = product.find_element(
                By.CSS_SELECTOR, 'input[type="hidden"][id^="ProductInfoPrice_"]'
            )
            price_raw = price_input_element.get_attribute('value')
            print(f"начальный вид цены: {price_raw}")
            price = price_raw.replace('\u00A0', '').replace(' ', '').replace('\u2009', '')
            price = price.replace('₽', '').replace(',', '.').strip()
            print(f"итоговый вид цены: {price}")

            try:
                price_float = float(price)
            except ValueError:
                print(f"        {j + 1}. ошибка: не удалось преобразовать цену '{price_raw}' в число, пропускаю товар")
                continue

            products_to_insert.append((category_name, name, price_float, product_url, 'okey'))

        except Exception as e:
            print(f"        {j + 1}. ошибка парсинга товара: {e}")
            continue

    if products_to_insert:
        try:
            before = conn.total_changes
            cursor.executemany(
                '''INSERT OR IGNORE INTO okey_products (category, name, price, url, shop) 
                   VALUES (?, ?, ?, ?, ?)''', products_to_insert)
            conn.commit()
            inserted = conn.total_changes - before
            print(f"    записано {inserted} новых товаров в БД")
        except Exception as e:
            print(f"    ошибка при записи в БД: {e}")

    conn.close()
    return True


initialize_db()

driver = create_stealth_driver()
try:
    print("открываю главную страницу каталога")
    driver.get("https://www.okeydostavka.ru/spb/catalog")
    time.sleep(random.uniform(3, 5))

    all_category_links = get_category_links(driver)
    main_category_urls = all_category_links[5:]

    print(f"найдено основных категорий (уровень 1): {len(main_category_urls)}")
    print("-" * 50)

    for i, (main_category_name, main_category_url) in enumerate(main_category_urls, start=1):
        try:
            print(f"уровень 1: обрабатываю категорию {i}: {main_category_name}")
            driver.get(main_category_url)
            time.sleep(random.uniform(15, 25))

            products_found = parse_products_on_page(driver, main_category_name)

            if not products_found:
                sub_category_urls = get_category_links(driver)
                print(f"  найдено подкатегорий (уровень 2): {len(sub_category_urls)}")

                for j, (sub_category_name, sub_category_url) in enumerate(sub_category_urls, start=1):
                    try:
                        full_category_name_2 = f"{main_category_name} / {sub_category_name}"
                        print(f"уровень 2: обрабатываю подкатегорию {j}: {full_category_name_2}")
                        driver.get(sub_category_url)
                        time.sleep(random.uniform(10, 18))

                        products_found_2 = parse_products_on_page(driver, full_category_name_2)

                        if not products_found_2:
                            inner_sub_category_urls = get_category_links(driver)
                            print(f"    найдено внутренних подкатегорий (уровень 3): {len(inner_sub_category_urls)}")

                            for k, (inner_sub_category_name, inner_sub_category_url) in enumerate(
                                    inner_sub_category_urls, start=1):
                                try:
                                    full_category_name_3 = f"{full_category_name_2} / {inner_sub_category_name}"
                                    print(f"уровень 3: обрабатываю внутреннюю подкатегорию {k}: {inner_sub_category_name}")
                                    driver.get(inner_sub_category_url)
                                    time.sleep(random.uniform(8, 15))

                                    parse_products_on_page(driver, full_category_name_3)

                                except Exception as e:
                                    print(f"ошибка во внутренней подкатегории {k}: {e}")
                                    continue

                    except Exception as e:
                        print(f"ошибка в подкатегории {j}: {e}")
                        continue

        except Exception as e:
            print(f"ошибка в основной категории {i}: {e}")
            continue

finally:
    print("\nскрипт завершен, закрываю драйвер")
    driver.quit()