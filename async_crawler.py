from urllib.parse import urljoin, urlparse, urldefrag
import threading
import time
import requests
from urllib.robotparser import RobotFileParser
import asyncio
from bs4 import BeautifulSoup
import os

class Crawler:
  def __init__(self, root_url: str, max_pages: int, delay: float, output_dir: str, num_workers: int):
    self.root_url = root_url
    self.max_pages = max_pages
    self.delay = delay
    self.visited = set()
    self.queue = asyncio.Queue()
    self.output_dir = output_dir
    self.num_workers = num_workers
    
    self.visited_lock = asyncio.Lock()
    self.queue_lock = asyncio.Lock()
    self.finish = asyncio.Event()
    self.rate_limit_lock = asyncio.Lock()
    self.user_agent = "WebCrawler/1.0 (Educational Purpose; +https://example.com/bot)"
    self.last_request_time = time.time()

  async def fetch_page(self, wid: int, url: str):
    async with self.visited_lock:
      if url in self.visited:
        return
      if len(self.visited) >= self.max_pages:
        self.finish.set()
        return
      self.visited.add(url)
    async with self.rate_limit_lock:
      elapsed = time.time() - self.last_request_time
      if elapsed < self.delay:
        await asyncio.sleep(self.delay - elapsed)
        self.last_request_time =  time.time()
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    try:
      rp = RobotFileParser(urljoin(base_url, "robots.txt"))
      rp.read()
      if not rp.can_fetch(self.user_agent, url):
        return None
      response = await asyncio.to_thread(requests.get, url, headers={"User-Agent": self.user_agent})
    except Exception as e:
      print(f"Error fetching {url}: {e}")
      return None
    # dump the response to a file
    filename = f"{self.output_dir}/{parsed.netloc}/{parsed.path}"
    if filename.endswith("/"):
      filename = filename + "index"
    filename += ".html"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w") as f:
      f.write(response.text)
    return response.text
    
  async def parse(self, text: str, base_url: str):
    # identify the nested pages
    soup = BeautifulSoup(text, "html.parser")
    for link in soup.find_all("a"):
      href = link.get("href")
      if href is None:
        continue
      href = urljoin(base_url, href)
      href, _ = urldefrag(href)
      scheme = urlparse(href).scheme
      if scheme not in ["http", "https"]:
        continue
      async with self.visited_lock:
        if href in self.visited:
          continue
        await self.queue.put(href)
      
  async def worker(self, wid: int):
    print(f"started worker {wid}")
    while True:
      try:
        url = await self.queue.get()
      except asyncio.QueueEmpty:
        if self.finish.is_set():
          break
        continue
      try:
        text = await self.fetch_page(wid, url)
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        if text is not None:
          await self.parse(text, base_url)
      finally:
        self.queue.task_done()

  async def crawl(self):
    print("started crawling")
    self.session = requests.Session()
    await self.queue.put(self.root_url)
    tasks =  [asyncio.create_task(self.worker(i)) for i in range(self.num_workers)]
    print("started workers")
    await self.queue.join()
    print("queue is empty")
    for task in tasks:
      task.cancel()
    print("finished crawling")

if __name__ == "__main__":
  crawler =  Crawler("https://chandlerzuo.github.io", 2, 1.0, "output", 1)
  asyncio.run(crawler.crawl())
        
