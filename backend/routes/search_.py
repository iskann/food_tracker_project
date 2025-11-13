from flask import Blueprint, render_template, request
from backend.extensions import db
from backend.models import Product

search_ = (Blueprint('search_', __name__))
@search_.route('/search')
def search_page():
    query = request.args.get('query', '').strip()
    results = []
    if query:
        results = Product.query.filter(Product.name.ilike(f"%{query}%")).all()
    return render_template('results.html', query=query, results=results)
