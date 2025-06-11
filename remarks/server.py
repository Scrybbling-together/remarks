import logging
import os.path

from flask import Flask, request

import remarks
import sentry_sdk

app = Flask("Remarks http server")

# Initialize Sentry
sentry_dsn = os.getenv('SENTRY_DSN')
if not sentry_dsn:
    logging.warning("Sentry DSN is missing. Error reporting will be disabled.")
else:
    sentry_sdk.init(dsn=sentry_dsn)
    logging.info("Initialized Sentry")


def main_prod():
    """Production entry point using Gunicorn"""
    import gunicorn.app.wsgiapp as wsgi
    import sys

    # Gunicorn configuration
    sys.argv = [
        'gunicorn',
        '--bind', '0.0.0.0:5000',
        '--workers', '2',
        '--worker-class', 'sync',
        '--timeout', '300',  # 5 minutes for file processing
        '--max-requests', '1000',
        '--max-requests-jitter', '100',
        'remarks.server:app'
    ]

    wsgi.run()


@app.post("/process")
def process():
    params = request.get_json()

    if not params or 'in_path' not in params or 'out_path' not in params:
        return {"error": "Missing required parameters"}, 400

    in_path = params['in_path']
    out_path = params['out_path']

    if not os.path.exists(in_path):
        return {"error": f"Input path does not exist: {in_path}"}, 400
    if not os.path.exists(out_path):
        return {"error": f"Output path does not exist: {out_path}"}, 400

    try:
        remarks.run_remarks(in_path, out_path)
        return {"status": "success"}, 200
    except Exception as e:
        logging.error(f"Processing failed: {e}")
        sentry_sdk.capture_exception(e)
        return {"error": "Processing failed"}, 500

@app.route("/health")
def health():
    return {"status": "healthy"}, 200

def main():
    app.run(host="0.0.0.0", port=5000)

if __name__ == "__main__":
    main()
