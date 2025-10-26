from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, urldefrag
from urllib.robotparser import RobotFileParser
import os
import asyncio
import time
from typing import List, Set, Tuple
import requests

async def process_url(url: str, agent:str) -> Tuple[str, List[str]]:
  html_text = ""
  new_urls: List[str] = []
  # download the text
  parsed = urlparse(url)
  rp = RobotFileParser(urljoin(f"{parsed.scheme}://{parsed.netloc}", "robot.txt"))
  rp.read()
  if rp.can_fetch(url, agent):
    try:
      response = await asyncio.to_thread(requests.get, url, headers = {"User-Agent": agent})
    except Exception as e:
      print(f"Error fetching {url}: {e}")
      return html_text, new_urls
    # extract other links
    html_text = response.text
    soup = BeautifulSoup(html_text, "html.parser")
    for field in soup.find_all(["a", "link"]):
      href = field.get("href")
      if href and isinstance(href, str):
        new_url = urljoin(url, href)
        new_url, _ = urldefrag(new_url)
        if urlparse(new_url).scheme in ["http", "https"]:
          new_urls.append(new_url)
  return html_text, new_urls	


class Crawler:
  def __init__(self, root_url: str, output_dir: str):
    self.root_url = root_url
    self.output_dir = output_dir
    self.queue = asyncio.Queue()
    self.agent = "Agent for Education"

    self.visited: Set[str] = set()
    self.visited_lock = asyncio.Lock()

    self.is_running = asyncio.Event()

  async def worker(self, wid):
    print(f"Worker {wid} started")
    while True:
      # dequeue and process
      url = ""
      try:
        url = self.queue.get_nowait()
      except asyncio.QueueEmpty:
        if self.is_running.is_set():
          print(f"Worker {wid} sees an empty queue.")
          break
        # wait for 3s
        if time.time() - self.last_crawl_time > 3:
            print(f"Worker {wid} timed out.")
            break
        await asyncio.sleep(1)
        continue
      self.queue.task_done()
      self.last_crawl_time = time.time()
      if self.is_running.is_set():
        continue
      try:
        html_text, new_urls = await process_url(url, agent = self.agent)
      except Exception as e:
        print(f"Error processing url: {e}")
        continue
      parsed = urlparse(url)
      # save to file
      filename = f"{self.output_dir}/{parsed.netloc}/{parsed.path}"
      if filename.endswith("/"):
        filename += "index"
      filename += ".html"
      os.makedirs(os.path.dirname(filename), exist_ok = True)
      try:
        with open(filename, "w") as f:
          f.write(html_text)
      except Exception as e:
        print(f"Error writing file to {filename}: {e}")
        pass
      async with self.visited_lock:
        self.visited.add(url)
        for x in new_urls:
          if x not in self.visited:
            await self.queue.put(x)
    print(f"Worker {wid} stopped.")

  async def check_max_pages(self, max_pages):
    print("Started checking max pages.")
    while not self.is_running.is_set():
      async with self.visited_lock:
        print(f"Visited {len(self.visited)} pages")
        if len(self.visited) >= max_pages:
          self.is_running.set()
          print("Reached max pages.")
          break
      await asyncio.sleep(1)

  async def run(self, num_workers: int, max_pages):
    print("Crawler started")
    await self.queue.put(self.root_url)
    print(f"queue size {self.queue.qsize()}")
    print("Crawler added root_url")
    self.last_crawl_time = time.time()
    tasks = [asyncio.create_task(self.worker(i)) for i in range(num_workers)]
    tasks.append(asyncio.create_task(self.check_max_pages(max_pages)))
    await asyncio.sleep(3)
    print("Crawler waiting for queue to be empty.")
    await self.queue.join()
    print("Queue is empty.")
    # [t.cancel() for t in tasks]
    await asyncio.gather(*tasks, return_exceptions=False)

if __name__ == "__main__":
  crawler = Crawler("http://chandlerzuo.github.io", "output")
  asyncio.run(crawler.run(num_workers=3, max_pages=5))
