from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/category')
def category():
    return render_template('category.html')

if __name__ == '__main__':
    app.run(debug=True)