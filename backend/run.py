# Entry point for running the Flask dev server (`python run.py`).
from app import create_app

app = create_app(run_checks=True)

if __name__ == "__main__":
    app.run(debug=True, port=5001)
