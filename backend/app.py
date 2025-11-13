from flask import Flask
from routes.main import main
from routes.api import api

app = Flask(
    __name__,
    template_folder='../frontend/templates',
    static_folder='../frontend/static'
)


app.register_blueprint(main)
app.register_blueprint(api)

if __name__ == '__main__':
    app.run(debug=True)
