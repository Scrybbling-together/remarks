import os
import os.path

from flask import Flask, request

import remarks

app = Flask("Remarks http server")

@app.post("/process")
def process():
    params = request.get_json()

    assert 'in_path' in params, "Missing parameter: in_path"
    assert 'out_path' in params, "Missing parameter: out_path"

    in_path = params['in_path']
    out_path = params['out_path']

    assert os.path.exists(in_path), f"Path does not exist: {in_path}"
    assert os.path.exists(out_path), f"Path does not exist: {out_path}"

    print(f"Got a request to process {params['in_path']}")

    parent_dir = in_path
    parent_dir = os.path.dirname(parent_dir)
    out_dir = os.path.join(parent_dir, "out")

    print(f"Making directory {out_dir}")
    os.makedirs(out_dir)

    result = remarks.run_remarks(in_path, out_dir)

    return "OK"

def main():
    app.run(host="0.0.0.0", port=5000)

if __name__ == "__main__":
    main()
