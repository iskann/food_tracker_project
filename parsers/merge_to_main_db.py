import os
import sqlite3

from backend.app import app
from backend.extensions import db
from backend.models import Store, Category, Product
from rapidfuzz import fuzz
from fuzzywuzzy import fuzz as fw_fuzz


BASE_DIR = os.path.dirname(__file__)
OKEY_DB_PATH = os.path.join(BASE_DIR, "okey_products.db")
SVETOFOR_DB_PATH = os.path.join(BASE_DIR, "svetofor_products.db")
MAIN_DB_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "data", "food_tracker.db"))


def _read_products(db_path: str, table_name: str):
    """читает все товары из указанной SQLite-БД и таблицы"""
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Не найдена БД: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT category, name, price, url, shop FROM {table_name}")
    rows = cursor.fetchall()
    conn.close()
    return rows


def _normalize_category(name: str) -> str:
    """нормализует название категории"""
    if not name:
        return ""
    norm = name.lower().strip()
    norm = norm.split("/")[0].strip()
    norm = norm.replace(",", " ")
    while "  " in norm:
        norm = norm.replace("  ", " ")
    return norm


def merge_databases():
    """объединяет данные из парсерных БД в основную БД приложения"""
    if os.path.exists(MAIN_DB_PATH):
        os.remove(MAIN_DB_PATH)
        print(f"🗑 Удалена старая основная БД: {MAIN_DB_PATH}")

    okey_rows_raw = _read_products(OKEY_DB_PATH, "okey_products")
    svetofor_rows_raw = _read_products(SVETOFOR_DB_PATH, "svetofor_products")

    def _to_dicts(rows):
        return [
            {
                "raw_category": row[0],
                "category_norm": _normalize_category(row[0]),
                "name": row[1],
                "price": row[2],
                "url": row[3],
                "shop": row[4],
            }
            for row in rows
        ]

    okey_rows = _to_dicts(okey_rows_raw)
    svetofor_rows = _to_dicts(svetofor_rows_raw)

    okey_categories_norm_raw = sorted({row["category_norm"] for row in okey_rows if row["category_norm"]})
    svetofor_categories_norm = sorted({row["category_norm"] for row in svetofor_rows if row["category_norm"]})

    INCOMPATIBLE_GROUPS = {
        "аптека": ["чай", "кофе", "напитки", "овощи", "фрукты", "молочные", "мясо", "рыба", "хлеб", "бакалея"],
        "лекарства": ["чай", "кофе", "напитки", "овощи", "фрукты", "молочные", "мясо", "рыба", "хлеб", "бакалея"],
        "медицина": ["чай", "кофе", "напитки", "овощи", "фрукты", "молочные", "мясо", "рыба", "хлеб", "бакалея"],
    }
    
    def _are_categories_compatible(cat1: str, cat2: str) -> bool:
        """проверяет, совместимы ли две категории для объединения"""
        cat1_words = set(cat1.split())
        cat2_words = set(cat2.split())
        
        for incompatible_word, incompatible_list in INCOMPATIBLE_GROUPS.items():
            if incompatible_word in cat1_words:
                if cat2_words & set(incompatible_list):
                    return False
            if incompatible_word in cat2_words:
                if cat1_words & set(incompatible_list):
                    return False
        
        return True
    
    def _calculate_category_similarity(cat1: str, cat2: str) -> float:
        """вычисляет похожесть двух категорий"""
        scores = [
            fuzz.ratio(cat1, cat2),
            fuzz.token_set_ratio(cat1, cat2),
            fuzz.token_sort_ratio(cat1, cat2),
            fw_fuzz.ratio(cat1, cat2),
            fw_fuzz.token_set_ratio(cat1, cat2),
        ]
        return max(scores)
    
    okey_categories_norm = sorted(set(okey_categories_norm_raw))
    
    print(f"Уникальных нормализованных категорий Окей (до объединения): {len(okey_categories_norm_raw)}")
    print(f"Уникальных нормализованных категорий Окей (после объединения одинаковых): {len(okey_categories_norm)}")
    
    category_mapping = {}
    
    for svetofor_norm in svetofor_categories_norm:
        best_match = None
        best_score = 0
        for okey_norm in okey_categories_norm:
            if not _are_categories_compatible(svetofor_norm, okey_norm):
                continue
            
            score = _calculate_category_similarity(svetofor_norm, okey_norm)
            if score > best_score:
                best_score = score
                best_match = okey_norm
        if best_match and best_score >= 75:
            category_mapping[svetofor_norm] = best_match
        else:
            category_mapping[svetofor_norm] = svetofor_norm

    for row in svetofor_rows:
        if row["category_norm"] in category_mapping:
            row["category_norm"] = category_mapping[row["category_norm"]]

    all_categories_norm = set(okey_categories_norm) | set(category_mapping.values())

    print(f"Уникальных нормализованных категорий Окей: {len(okey_categories_norm)}")
    print(f"Уникальных нормализованных категорий Светофор: {len(svetofor_categories_norm)}")
    print(f"Всего категорий после объединения: {len(all_categories_norm)}")

    if not all_categories_norm:
        print("⚠ Нет категорий для объединения.")
        return

    with app.app_context():
        db.create_all()

        store_map = {}
        for code, display_name in (("okey", "Окей"), ("svetofor", "Светофор")):
            store = Store(name=display_name)
            db.session.add(store)
            store_map[code] = store

        def _display_name_for(norm_name: str) -> str:
            for row in svetofor_rows:
                if row["category_norm"] == norm_name and row["raw_category"]:
                    return row["raw_category"]
            for row in okey_rows:
                if row["category_norm"] == norm_name and row["raw_category"]:
                    return row["raw_category"]
            return norm_name.title()

        category_map = {}
        for norm_name in sorted(all_categories_norm):
            display_name = _display_name_for(norm_name)
            category = Category(name=display_name, image=None)
            db.session.add(category)
            category_map[norm_name] = category

        db.session.commit()

        def _add_products(rows):
            for row in rows:
                norm_cat = row["category_norm"]
                if not norm_cat or norm_cat not in all_categories_norm:
                    continue

                store = store_map.get(row["shop"])
                if not store:
                    continue

                cat_obj = category_map.get(norm_cat)
                if not cat_obj:
                    continue

                try:
                    price_value = float(row["price"])
                except (TypeError, ValueError):
                    continue

                product = Product(
                    name=row["name"],
                    price=price_value,
                    store=store,
                    category=cat_obj,
                )
                db.session.add(product)

        _add_products(okey_rows)
        _add_products(svetofor_rows)

        db.session.commit()
        print("✅ Данные из парсеров успешно загружены в основную БД.")


if __name__ == "__main__":
    merge_databases()


