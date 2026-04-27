import os
from app import create_app
from config import Config, TestConfig

mode = os.getenv('FLASK_ENV', 'production')
config = TestConfig if mode == 'testing' else Config


app = create_app(config)

if __name__ == '__main__':
    # El 0.0.0.0 le dice a Flask: "Acepta conexiones de cualquier dispositivo en el Wi-Fi"
    app.run(host='0.0.0.0', port=5000, debug=True) 