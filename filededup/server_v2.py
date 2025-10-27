from flask import Flask, jsonify, request
from typing import Dict, Set

app = Flask(__name__)

file_map: Dict[str, Set[str]] = {}

@app.route("/post", methods=["POST"])
def post():
  data = request.get_json()
  for fname, hash_val in data.items():
    file_map.setdefault(hash_val, set()).add(fname)
  return jsonify({"status": "succeed"})

@app.route("/get", methods=["GET"])
def get():
  return jsonify({k: list(v) for k, v in file_map.items()})

if __name__ == "__main__":
  app.run(host = "0.0.0.0", port = 9999)
