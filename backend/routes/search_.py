from flask import Blueprint, render_template, request
from backend.extensions import db
from backend.models import Product
from sqlalchemy import func

search_ = (Blueprint('search_', __name__))
@search_.route('/search')
def search_page():
    query = request.args.get('query', '').strip()
    results = []
    if query:
        query_lower = query.lower()
        results = Product.query.filter(
            func.lower(Product.name).like(f"%{query_lower}%")
        ).all()
    return render_template('results.html', query=query, results=results)
