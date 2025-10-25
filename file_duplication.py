import queue
import os
import threading
from typing import Dict, Tuple, Set
import hashlib

class FileDuplication:
    def __init__(self, root_dir: str):
        self.root_dir = str
        self.all_dirs = queue.Queue()
        self.all_dirs.put(root_dir)
        self.map: Dict[Tuple[int, int], Set[str]] = {}
        self.map_lock = threading.Lock()
        self.queue_lock = threading.Lock()

    def process_dir(self, dir: str):
        files = [f for f in os.listdir(dir) if os.path.isfile(os.path.join(dir, f))]
        file_stats: Dict[Tuple[int, int], Set[str]] = {}
        for f in files:
            f = f"{dir}/{f}"
            size = os.path.getsize(f)
            rsum = self.rsum(f)
            if (size, rsum) not in file_stats:
                file_stats[(size, rsum)] = set()
            file_stats[(size, rsum)].add(f"{dir}/{f}")
        return file_stats     

    def rsum(self, fname:str):
        ret = 0
        with open(fname, 'rb') as f:
            while chunk := f.read(8192):
                hashfunc = hashlib.new("sha256")
                hashfunc.update(chunk)
                hashval = hashfunc.hexdigest()
                ret += int(hashval, 16)
        return ret

    def worker(self):
        while True:
            try:
                with self.queue_lock:
                    dir = self.all_dirs.get(block=False)
                    child_dirs = [f"{dir}/{d}" for d in os.listdir(dir) if os.path.isdir(os.path.join(dir, d))]
                    for d in child_dirs:
                        self.all_dirs.put(d)
            except queue.Empty:
                print(f"{threading.current_thread().name} is done")
                break
            print(f"{threading.current_thread().name} is processing {dir}")
            file_stats = self.process_dir(dir)
            print(f"{threading.current_thread().name} processed {dir}")
            with self.map_lock:
                for k, v in file_stats.items():
                    if k not in self.map:
                        self.map[k] = v
                    else:
                        self.map[k] = self.map[k].union(v)

    def run(self, num_workers: int):
        threads = []
        for _ in range(num_workers):
            t = threading.Thread(target = self.worker)
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
            print(f"{t.name} joined")

        return self.map

if __name__ == "__main__":
    fd = FileDuplication("output")
    dups = fd.run(2)
    for v in dups.values():
        print(" ".join(v))


