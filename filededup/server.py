from flask import Flask, request, jsonify
from typing import Dict, Tuple, Set

app = Flask(__name__)

file_map: Dict[str, Set[str]] = {}

@app.route('/submit', methods=['POST'])
def submit():
  data: Dict[str, Tuple[int, str]] = request.get_json()
  for k, v in data.items():
      file_map.setdefault(f"{v[1]}_{hex(v[0])}", set()).add(k)
  return jsonify({"status": "success"})

@app.route('/results', methods=['GET'])
def results():  
  return jsonify({k: list(v) for k, v in file_map.items()})

if __name__ == '__main__':
   app.run(host='0.0.0.0', port=8080)
