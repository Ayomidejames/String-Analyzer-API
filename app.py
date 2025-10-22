from flask import Flask, jsonify
from flask_cors import CORS
from models import init_db
from routes.strings import strings_bp
from routes.natural_filter import natural_bp

def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    CORS(app)
    
    app.config.setdefault("DATABASE_URL", "sqlite:///strings.db")
    if config:
        app.config.update(config)

    # initialize DB (creates tables)
    init_db(app.config["DATABASE_URL"])

    # register blueprints
    app.register_blueprint(strings_bp, url_prefix="/strings")
    app.register_blueprint(natural_bp, url_prefix="/strings")

    @app.route("/", methods=["GET"])
    def health():
        return jsonify({"status": "ok"}), 200

    return app

if __name__ == "__main__":
    # dev server
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)