from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import sqlite3
import random
import sys

# Установим лимит рекурсии
sys.setrecursionlimit(2000)

# Имя файла базы данных SQLite
DB_NAME = 'okey_products.db'


# --- Инициализация базы данных ---

def initialize_db():
    """Создает базу данных SQLite и таблицу для хранения продуктов."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Создаем таблицу с необходимыми столбцами.
    # 'Ссылка' (product_url) используется как PRIMARY KEY, чтобы избежать дубликатов
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
    print(f"✅ База данных '{DB_NAME}' и таблица 'okey_products' готовы.")


# --- Инициализация драйвера ---

def create_stealth_driver():
    """Создает и возвращает настроенный 'скрытый' Chrome WebDriver."""
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    # Используем ChromeDriverManager для автоматической установки драйвера
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    # Скрытие флага WebDriver
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver


# --- Вспомогательная функция для сбора ссылок на категории ---

def get_category_links(driver):
    """Находит и возвращает список кортежей (название, URL) для категорий на текущей странице."""
    category_links = []
    # Категории имеют общий класс "col-xs-5"
    category_blocks = driver.find_elements(By.CLASS_NAME, "col-xs-5")

    for cat_block in category_blocks:
        try:
            # Находим ссылку внутри заголовка H2
            link = cat_block.find_element(By.CSS_SELECTOR, "h2 a")
            # Собираем все, код обработки категорий сам отфильтрует то, что нужно.
            category_links.append((link.text.strip(), link.get_attribute("href")))
        except:
            continue

    return category_links


# --- Функция для парсинга товаров и записи в SQLite ---

def parse_products_on_page(driver, category_name):
    """Парсит товары на текущей странице и записывает их в базу данных SQLite. Возвращает True, если товары найдены."""

    # Ищем все элементы-товары (обычно это <li> внутри класса grid_mode)
    all_li = driver.find_elements(By.CSS_SELECTOR, ".grid_mode li")
    valid_products = []

    # Отфильтровываем только те <li>, которые содержат название товара
    for li in all_li:
        try:
            li.find_element(By.CSS_SELECTOR, ".product-name a")
            valid_products.append(li)
        except:
            continue

    print(f"    Найдено товаров: {len(valid_products)}")

    if not valid_products:
        return False  # Товары не найдены

    # Подключаемся к БД для записи данных
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    products_to_insert = []

    for j, product in enumerate(valid_products):
        try:
            name_link = product.find_element(By.CSS_SELECTOR, ".product-name a")
            name = name_link.text.strip()
            product_url = name_link.get_attribute("href")

            # Надежное получение цены из скрытого поля input
            price_input_element = product.find_element(
                By.CSS_SELECTOR, 'input[type="hidden"][id^="ProductInfoPrice_"]'
            )
            price = price_input_element.get_attribute('value').strip().replace(' ', '')
            price_cleaned = price.replace(' ', '').replace('₽', '')
            price_final = price_cleaned.replace(',', '.')
            # Преобразуем цену в число с плавающей точкой
            try:
                price_float = float(price_final[:-1])
            except ValueError:
                print(f"        {j + 1}. Ошибка: Не удалось преобразовать цену '{price}' в число. Пропускаю товар.")
                continue

            products_to_insert.append((category_name, name, price_float, product_url, 'okey'))

        except Exception as e:
            # Сюда попадут ошибки, если не найдены название/цена/ссылка конкретного товара
            print(f"        {j + 1}. Ошибка парсинга товара: {e}")
            continue

    # Массовая вставка данных в БД
    if products_to_insert:
        try:
            # Используем INSERT OR IGNORE для пропуска товаров, если их URL уже есть в БД
            cursor.executemany(
                '''INSERT OR IGNORE INTO okey_products (category, name, price, url, shop) 
                   VALUES (?, ?, ?, ?, ?)''', products_to_insert)
            conn.commit()
            print(f"    Успешно записано {cursor.rowcount} новых товаров в SQLite.")
        except Exception as e:
            print(f"    Ошибка при записи в SQLite: {e}")

    conn.close()
    return True  # Товары обработаны


# --- Основная логика ---

# Шаг 0: Инициализация базы данных
initialize_db()

driver = create_stealth_driver()
try:
    # Шаг 1: Открываем главную страницу каталога
    print("🚀 Открываю главную страницу каталога...")
    driver.get("https://www.okeydostavka.ru/spb/catalog")
    time.sleep(random.uniform(3, 5))

    # Шаг 2: Находим основные категории (УРОВЕНЬ 1)
    all_category_links = get_category_links(driver)

    # На главной странице каталога пропускаем первые 3 ссылки
    main_category_urls = all_category_links[5:]

    print(f"Найдено основных категорий (Уровень 1): {len(main_category_urls)}")
    print("-" * 50)

    # Шаг 3: Обрабатываем категории УРОВНЯ 1
    for i, (main_category_name, main_category_url) in enumerate(main_category_urls, start=1):
        try:
            print(f"🔥 УРОВЕНЬ 1: Обрабатываю категорию {i}: **{main_category_name}**")
            driver.get(main_category_url)
            time.sleep(random.uniform(15, 25))

            # 1. Попытка спарсить товары на главной странице категории (Уровень 1)
            products_found = parse_products_on_page(driver, main_category_name)

            # 2. Если товары НЕ найдены, ищем подкатегории (УРОВЕНЬ 2)
            if not products_found:
                sub_category_urls = get_category_links(driver)
                print(f"  Найдено подкатегорий (Уровень 2): {len(sub_category_urls)}")

                # Обход подкатегорий (УРОВЕНЬ 2)
                for j, (sub_category_name, sub_category_url) in enumerate(sub_category_urls, start=1):
                    try:
                        full_category_name_2 = f"{main_category_name} / {sub_category_name}"
                        print(f"  ⚡️ УРОВЕНЬ 2: Обрабатываю подкатегорию {j}: **{full_category_name_2}**")
                        driver.get(sub_category_url)
                        time.sleep(random.uniform(10, 18))

                        # 2.1. Попытка спарсить товары на странице подкатегории (Уровень 2)
                        products_found_2 = parse_products_on_page(driver, full_category_name_2)

                        # 2.2. Если товары НЕ найдены, ищем внутренние подкатегории (УРОВЕНЬ 3)
                        if not products_found_2:
                            inner_sub_category_urls = get_category_links(driver)
                            print(f"    Найдено внутренних подкатегорий (Уровень 3): {len(inner_sub_category_urls)}")

                            # Обход внутренних подкатегорий (УРОВЕНЬ 3)
                            for k, (inner_sub_category_name, inner_sub_category_url) in enumerate(
                                    inner_sub_category_urls, start=1):
                                try:
                                    full_category_name_3 = f"{full_category_name_2} / {inner_sub_category_name}"
                                    print(
                                        f"УРОВЕНЬ 3: Обрабатываю внутреннюю подкатегорию {k}: **{inner_sub_category_name}**")
                                    driver.get(inner_sub_category_url)
                                    time.sleep(random.uniform(8, 15))

                                    # Парсим товары на странице внутреннего уровня (Уровень 3)
                                    parse_products_on_page(driver, full_category_name_3)

                                except Exception as e:
                                    print(f"Ошибка в внутренней подкатегории {k}: {e}")
                                    continue

                    except Exception as e:
                        print(f"Ошибка в подкатегории {j}: {e}")
                        continue

        except Exception as e:
            print(f"Ошибка в основной категории {i}: {e}")
            continue

finally:
    print("\nСкрипт завершен. Закрываю драйвер.")
    driver.quit()