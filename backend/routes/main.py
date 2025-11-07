from flask import Blueprint, render_template, url_for

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/categories')
def categories():
    # Пример данных категорий
    categories = [
        {'id': 1, 'name': 'Хлеб', 'image': 'img/хлеб.jpg'},
    ]
    return render_template('categories.html', categories=categories)

@main.route('/category/<int:category_id>')
def category(category_id):
    # Примерная категория и товары
    categories = {
        1: {'name': 'Хлеб', 'products': [
            {'name': 'ООУУКЕЙ батон', 'prices': [{'store': {'name': 'доставка'}, 'price': 125}]},
            {'name': 'ОУУУКЕЕЙ хлеб', 'prices': [
                {'store': {'name': 'доставка'}, 'price': 50},
                {'store': {'name': 'magnit'}, 'price': 55}
            ]},
        ]},
    }

    category = categories.get(category_id)
    if not category:
        return "Категория не найдена", 404

    return render_template('category.html', category=category, products=category['products'])

@main.route('/about')
def about():
    return render_template('about.html')