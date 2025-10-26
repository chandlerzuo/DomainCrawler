from typing import Dict, Tuple
import hashlib
import os
import requests
import asyncio

root_dir = "output"
host = "localhost"
port = 8080

def scan_local() -> Dict[str, Tuple[int, str]]:
  # walk from root_dir, save results to self.file_map
  ret: Dict[str, Tuple[int, str]] = {}
  for dir, _, files in os.walk(root_dir):
    for fname in files:
      file_path = os.path.join(dir, fname)
      try:
        hashfunc = hashlib.sha256()
        file_size = 0
        with open(file_path, 'rb') as f:
          while chunk := f.read(1024 * 64):
            hashfunc.update(chunk)
            file_size += len(chunk)
        ret[file_path] = (file_size, hashfunc.hexdigest())
      except Exception:
        pass
  return ret

async def rescan():
  while True:
    print("started rescan")
    ret = scan_local()
    print("finished rescan")
    url = f"http://{host}:{port}/submit"
    try:
      _ = requests.post(url, json=ret)
    except Exception as e:
      print(f"Error from client: {e}")
      pass
    # sleep for 10 seconds
    await asyncio.sleep(5)

async def get_results():
  while True:
    url = f"http://{host}:{port}/results"
    try:
      response = requests.get(url)
      print(response.json())
    except Exception as e:
      print(f"Error getting results: {e}")
      pass
    await asyncio.sleep(5)

async def main():
  tasks = [asyncio.create_task(rescan()), asyncio.create_task(get_results())]
  await asyncio.gather(*tasks)

if __name__ == '__main__':
  asyncio.run(main())