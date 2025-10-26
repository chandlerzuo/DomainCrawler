import asyncio
import os
from typing import Dict, Set, Tuple
import hashlib
import json

class FileDedup:

  def __init__(self, root_dir: str, is_server: bool, host: str, port: int,
               machine_id: int):
    self.root_dir = root_dir
    self.host = host
    self.port = port
    self.machine_id = machine_id
    self.is_server = is_server
    self.is_running = False

    # storage
    self.file_map: Dict[Tuple[int, str], Set[str]] = {}
    self.map_lock = asyncio.Lock()

  async def scan_local(self) -> Dict[str, Tuple[int, str]]:
    # walk from root_dir, save results to self.file_map
    ret: Dict[str, Tuple[int, str]] = {}
    for dir, _, files in os.walk(self.root_dir):
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
        except Exception as e:
          pass
    return ret

  async def client_send_msg(self, writer: asyncio.StreamWriter):
    # send results to server
    while self.is_running:
      try:
        print(f'{self.machine_id} connected, write message')
        async with self.map_lock:
          msg = json.dumps(self.file_map).encode() + b'\n'
          writer.write(msg)
          await writer.drain()
          print(f'{self.machine_id} sent message')
      except (ConnectionResetError, ConnectionRefusedError) as e:
        print(f'{self.machine_id} connection error')
        pass
      except Exception as e:
        print(f'{self.machine_id} error: {e}')
        pass
      finally:
        writer.close()
        await writer.wait_closed()
        await asyncio.sleep(10)

  async def client_proc(self):
    self.is_running = True
    _, writer = await asyncio.open_connection(self.host, self.port)
    print(f'{self.machine_id} connected to server {self.host}:{self.port}')

    async def rescan():
      while self.is_running:
        print(f"started rescan for {self.machine_id}")
        await self.scan_local()
        print(f"finished rescan for {self.machine_id}")
        await asyncio.sleep(20)

    try:
      tasks = [
          asyncio.create_task(rescan()),
          asyncio.create_task(self.client_send_msg(writer))
      ]
      asyncio.gather(*tasks)
    except asyncio.CancelledError:
      pass

  async def server_reduce(self, reader: asyncio.StreamReader,
                          writer: asyncio.StreamWriter):
    print("server received data")
    while self.is_running:
      data = await reader.readline()
      data = json.loads(data.decode())
      async with self.map_lock:
        for fname, stats in data.items():
          self.file_map.setdefault(stats, set()).add(fname)
      await asyncio.sleep(10)

  async def server_proc(self):
    self.is_running = True
    print("started server")
    server = await asyncio.start_server(self.server_reduce, self.host,
                                        self.port)
    print(f"Server started, listening on {self.host}:{self.port}")
    async with server:

      async def print_result():
        while self.is_running:
          print("server aggregating results.")
          async with self.map_lock:
            for k, v in self.file_map.items():
              print(f'{k}: {v}')
          await asyncio.sleep(5)

      server_task = asyncio.create_task(print_result())
    try:
      await server.serve_forever()
    except Exception:
      server_task.cancel()

  def stop(self):
    self.is_running = False


if __name__ == '__main__':
  # start client
  host = "localhost"
  # error: port number must be from 1 to 65535
  port = 8080

  async def run():
    server = FileDedup(root_dir="",
                       is_server=True,
                       host="0.0.0.0",
                       port=port,
                       machine_id=0)
    server_task = asyncio.create_task(server.server_proc())
    await asyncio.sleep(10)
    client = FileDedup(root_dir="output",
                       is_server=False,
                       host=host,
                       port=port,
                       machine_id=1)
    client_task = asyncio.create_task(client.client_proc())

    await asyncio.sleep(15)
    client.stop()
    server.stop()
    asyncio.gather(client_task, server_task)

  asyncio.run(run())
