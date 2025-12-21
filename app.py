# app.py - entrypoint to launch the Flask app factory
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
