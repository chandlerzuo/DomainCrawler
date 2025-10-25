import asyncio
import hashlib
from typing import Dict, Tuple

class FileDedup:
  def __init__(self, root_dir):
    self.root_dir = root_dir
    self.queue = asyncio.Queue()
    self.map: Dict[Tuple(int, int), str] = {}

    self.queue_lock = asyncio.Lock()
    self.map_lock = asyncio.Lock()

  async def checksum(self, fname) -> Tuple[int, int]:
    fsum = 0
    with open(fname, ‘rb’) as f:
      while chunk := f.read(8192)
        hashfunc = hashlib.new(‘sha256’)
        hashfunc.update(chunk)
        hashval = hashfunc.hexdigest()
        fsum += int(hashval, 16)
    return os.path.getsize(fname), fsum

  async def process(self, wid: int):
    while True:
      try:
      dir = self.queue.get_nowait()
    except asyncio.QueueEmpty:
      break

    paths = await async.to_thread(os.listdir(dir))
    files = [f’{dir}/{f}’ for f in paths if os.path.isfile(f’{dir}/{f}’)]
    subdirs = [f’{dir}/{f} for f in paths if not os.path.isfile(f’{dir}/{f}’)]

    [self.queue.put(x) for x in subdirs]

    map_update = {}
    for fname in files:
      map_update[fname] = await self.checksum(fname)
    async with self.map_lock:
        for k, v in map_update.items():
          self.map.setdefault(v, {})[v].add(k)
      self.queue.task_done()

  async run(self, num_workers: int):
    await self.queue.put(self.root_dir)

    workers = [asyncio.create_task(self.process(i)) for i in range(num_workers)]

    self.queue.join()
    [w.cancel() for w in workers]

