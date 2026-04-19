import os

from app import create_app


config_name = os.environ.get("FLASK_CONFIG", "development")
app = create_app(config_name)


if __name__ == "__main__":
    app.run(
        host=app.config["LISTEN_HOST"],
        port=app.config["LISTEN_PORT"],
        debug=app.config["DEBUG"],
    )
