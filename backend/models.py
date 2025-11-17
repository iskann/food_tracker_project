from backend.extensions import db


class Store(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"<Store {self.name}>"

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    image = db.Column(db.String(100))

    def __repr__(self):
        return f"<Category {self.name}>"

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float)
    store_id = db.Column(db.Integer, db.ForeignKey('store.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))

    store = db.relationship('Store', backref='products')
    category = db.relationship('Category', backref='products')

    def __repr__(self):
        return f"<Product {self.name}>"
