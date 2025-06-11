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

@app.post("/process")
def process():
    params = request.get_json()

    if 'in_path' not in params:
        logging.error("Missing parameter: in_path")
    if 'out_path' not in params:
        logging.error("Missing parameter: out_path")

    in_path = params['in_path']
    out_path = params['out_path']

    if not os.path.exists(in_path):
        logging.error(f"In path does not exist: {in_path}")
    if not os.path.exists(out_path):
        logging.error(f"Out path does not exist: {out_path}")

    logging.info(f"Got a request to process {params['in_path']}")

    try:
        parent_dir = in_path
        parent_dir = os.path.dirname(parent_dir)
        out_dir = os.path.join(parent_dir, "out")

        logging.info(f"Making directory {out_dir}")
        os.makedirs(out_dir)

        remarks.run_remarks(in_path, out_dir)
    except Exception as e:
        logging.error(e)
        sentry_sdk.capture_exception(e)
        return e

    return "OK"

def main():
    app.run(host="0.0.0.0", port=5000)

if __name__ == "__main__":
    main()
