from flask import Flask
from backend.routes.search_ import search_
from backend.routes.main import main
from backend.extensions import db

app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static",
)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///../data/food_tracker.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# импортируем модели для создания таблиц
from backend.models import Product, Category, Store  # noqa: E402,F401

app.register_blueprint(main)
app.register_blueprint(search_)


if __name__ == "__main__":
    with app.app_context():
        # создаём таблицы, данные заполняются отдельным скриптом
        db.create_all()

    app.run(debug=True)