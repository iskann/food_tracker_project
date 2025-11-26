from flask import Blueprint, render_template
from backend.models import Product, Category
from rapidfuzz import fuzz
from fuzzywuzzy import fuzz as fw_fuzz
import random
import re

main = Blueprint("main", __name__)


def _normalize_product_name(name: str) -> str:
    """нормализация имени товара: нечувствительно к регистру, по словам"""
    if not name:
        return ""
    s = name.lower()
    s = re.sub(r"[^0-9a-zа-яё]+", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def _calculate_similarity(name1: str, name2: str) -> float:
    """
    вычисляет похожесть двух названий товаров, используя несколько методов
    возвращает максимальный score из разных алгоритмов
    """
    n1 = _normalize_product_name(name1)
    n2 = _normalize_product_name(name2)
    
    if not n1 or not n2:
        return 0.0
    
    scores = [
        fuzz.ratio(n1, n2),
        fuzz.token_set_ratio(n1, n2),
        fuzz.token_sort_ratio(n1, n2),
        fuzz.partial_ratio(n1, n2),
        fw_fuzz.ratio(n1, n2),
        fw_fuzz.token_set_ratio(n1, n2),
        fw_fuzz.partial_ratio(n1, n2),
    ]
    
    return max(scores)


@main.route("/")
def index():
    products = Product.query.all()
    random_cards = random.sample(products, min(len(products), 4)) if products else []
    return render_template("index.html", cards=random_cards)


@main.route("/categories")
def categories():
    categories_list = Category.query.order_by(Category.name).all()
    return render_template("categories.html", categories=categories_list)


@main.route("/category/<int:category_id>")
def category(category_id):
    category_obj = Category.query.get_or_404(category_id)
    products = Product.query.filter_by(category_id=category_id).all()

    # группируем товары, которые есть в обоих магазинах
    by_norm = {}
    for p in products:
        key = _normalize_product_name(p.name)
        by_norm.setdefault(key, []).append(p)

    in_both = []
    remaining = []

    for key, plist in by_norm.items():
        stores = {p.store.name for p in plist}
        if len(stores) >= 2:
            in_both.append({"name": plist[0].name, "products": plist})
        else:
            remaining.extend(plist)

    # группируем похожие товары
    similar_groups = []
    used_ids = set()

    threshold_min = 50
    threshold_max = 95
    
    remaining_sorted = sorted(remaining, key=lambda p: _normalize_product_name(p.name))
    
    for i, p1 in enumerate(remaining_sorted):
        if p1.id in used_ids:
            continue
        
        group = [p1]
        group_normalized = _normalize_product_name(p1.name)
        
        for p2 in remaining_sorted[i + 1:]:
            if p2.id in used_ids:
                continue
            
            score = _calculate_similarity(p1.name, p2.name)
            
            if threshold_min <= score < threshold_max:
                group.append(p2)
                used_ids.add(p2.id)
                p2_normalized = _normalize_product_name(p2.name)
                if len(p2_normalized) < len(group_normalized):
                    group_normalized = p2_normalized
        
        if len(group) > 1:
            products_by_store = {}
            for p in group:
                store_name = p.store.name
                if store_name not in products_by_store:
                    products_by_store[store_name] = []
                products_by_store[store_name].append(p)
            
            group_display_name = min(group, key=lambda p: len(p.name)).name
            
            similar_groups.append({
                "name": group_display_name,
                "products": group,
                "products_by_store": products_by_store
            })
            for p in group:
                used_ids.add(p.id)

    unique_products = [p for p in remaining if p.id not in used_ids]

    return render_template(
        "category.html",
        category=category_obj,
        in_both=in_both,
        similar_groups=similar_groups,
        unique_products=unique_products,
    )


@main.route("/about")
def about():
    return render_template("about.html")