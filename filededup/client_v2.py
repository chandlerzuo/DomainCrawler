import os
import hashlib
import asyncio
import requests
from typing import Dict, Optional

def calc_filehash(fpath) -> Optional[str]:
  try:
    fsize = 0
    hashfunc = hashlib.sha256()
    with open(fpath, 'rb') as f:
      while chunk := f.read(1024*64):
        hashfunc.update(chunk)
        fsize += len(chunk)
    return f"{hashfunc.hexdigest()}_{hex(fsize)}"
  except:
    return None

async def scan_dir(root_dir: str) -> Dict[str, str]:
  file_stats: Dict[str, str] = {}
  for dir, _, files in os.walk(root_dir):
    for fname in files:
      fpath = os.path.join(dir, fname)
      file_hash = calc_filehash(fpath)
      if file_hash:
        file_stats[fpath] = file_hash
  return file_stats

class FileHash:
  def __init__(self, root_dir: str, host: str, port: int, update_interval: int):
    self.root_dir = root_dir
    self.update_interval = update_interval
    self.server_url = f"http://{host}:{port}"
    self.finish = asyncio.Event()
    self.update_interval = update_interval

  async def rescan(self):
    while not self.finish.is_set():
      file_stats = await scan_dir(self.root_dir)
      try:
        _ = requests.post(f"{self.server_url}/post", json=file_stats)
      except Exception as e:
        print(f"POST error: {e}")
      await asyncio.sleep(self.update_interval)

  async def get_results(self):
    while not self.finish.is_set():
      try:
        response = requests.get(f"{self.server_url}/get")
        if response.status_code == 200:
          print("GET results:")
          for k, v in response.json().items():
            print(f"{k}: {v}")
        else:
          print(f"GET error: {response.status_code}")
      except Exception as e:
        print(f"{e}")
      await asyncio.sleep(self.update_interval)

  async def run(self, server_runtime: int):
    tasks = [asyncio.create_task(self.rescan()), asyncio.create_task(self.get_results())]
    await asyncio.sleep(server_runtime)
    self.finish.set()
    await asyncio.gather(*tasks)

if __name__ == "__main__":
  client = FileHash(root_dir = "output", host = "localhost", port = 9999, update_interval = 3)
  asyncio.run(client.run(server_runtime = 10))