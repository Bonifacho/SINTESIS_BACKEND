import os
from app import create_app
from config import Config, TestConfig

mode = os.getenv('FLASK_ENV', 'production')
config = TestConfig if mode == 'testing' else Config


app = create_app(config)

if __name__ == '__main__':
    app.run(debug=(mode == 'testing'), port=5000) 