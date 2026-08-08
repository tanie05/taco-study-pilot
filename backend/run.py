# Entry point for running the Flask dev server (`python run.py`).
from app import create_app

app = create_app(run_checks=True)

if __name__ == "__main__":
    # threaded=True so SSE connections (see /workspace/<id>/events) don't
    # block the single dev-server thread from serving other requests.
    app.run(debug=True, port=5001, threaded=True)
