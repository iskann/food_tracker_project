from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from backend.routes.search_ import search_
from routes.main import main
from backend.extensions import db

app = Flask(
    __name__,
    template_folder='../frontend/templates',
    static_folder='../frontend/static'
)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../data/food_tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

from backend.models import Product, Category, Store

app.register_blueprint(main)
app.register_blueprint(search_)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        if not Category.query.first():
            bread = Category(name='Хлеб', image='img/хлеб.jpg')
            magnit = Store(name='Магнит')
            okey = Store(name='Окей')
            db.session.add_all([bread, magnit, okey])
            db.session.commit()

            product1 = Product(name='Батон Окей', price=125, store=okey, category=bread)
            product2 = Product(name='Хлеб Магнит', price=55, store=magnit, category=bread)
            db.session.add_all([product1, product2])
            db.session.commit()

    app.run(debug=True)