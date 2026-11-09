import os
from app import create_app
from config import Config, TestConfig, IS_PRODUCTION

mode = os.getenv('FLASK_ENV', 'production')
config = TestConfig if mode == 'testing' else Config


app = create_app(config)

if __name__ == '__main__':
    # En producción el modo debug interactivo (Werkzeug debugger) permanece siempre desactivado
    debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() == 'true' and not IS_PRODUCTION
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
