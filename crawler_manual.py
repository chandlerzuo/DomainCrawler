from bs4 import BeautifulSoup
from typing import Set
from urllib.parse import urljoin, urldefrag, urlparse
from urllib.robotparser import RobotFileParser
import requests
import os
import time
import queue
import threading


def get_outbound_links(text: str, base_url: str) -> Set[str]:
  ret: Set[str] = set()
  try:
    soup = BeautifulSoup(text, "html.parser")
    for tag in soup.find_all(["a", "link"]):
      href = tag.get("href")
      if not href or not isinstance(href, str):
        continue
      url = urljoin(base_url, href)
      url = urldefrag(url).url
      parsed = urlparse(url)
      if parsed.scheme in {"http", "https"}:
        ret.add(url)

  except Exception as e:
    print(f"Error parsing HTML: {str(e)}")
    return ret
  return ret


def construct_filepath(output_dir: str, domain: str, path: str) -> str:
  filepath = os.path.join(output_dir, domain, path.lstrip("/"))
  if path == "" or path.endswith("/"):
    filepath += "index"
  filepath = filepath + ".html"
  try:
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
  except Exception as e:
    pass
  return filepath


class Crawler:

  def __init__(self, seed_url: str, delay: float, output_dir: str,
               max_pages: int, num_workers: int):
    self.seed_url = seed_url
    self.session = requests.Session()
    self.visited_url: Set[str] = set()
    self.queue = queue.Queue()
    self.queue.put(seed_url)
    self.max_pages = max_pages
    self.output_dir = output_dir
    if not os.path.exists(output_dir):
      os.makedirs(output_dir)
    self.agent = "WebCrawler/1.0 Educational Purpose"
    self.delay = delay
    self.num_workers = num_workers
    self.last_request_time = time.time()
    self.finish_crawl = threading.Event()

    self.queue_lock = threading.Lock()
    self.visited_lock = threading.Lock()
    self.rate_limit_lock = threading.Lock()

  def fetch_page(self, url: str):
    outbound_links: Set[str] = set()
    try:
      with self.rate_limit_lock:
        elapsed = time.time() - self.last_request_time
        if elapsed < self.delay:
          time.sleep(self.delay - elapsed)
          self.last_request_time = time.time()
      response = self.session.get(url, timeout=10, allow_redirects=True)
      text = response.text
      outbound_links = get_outbound_links(text, url)
      with self.visited_lock:
        outbound_links = outbound_links - self.visited_url
        with self.queue_lock:
          for link in outbound_links:
            if not self.finish_crawl.is_set():
              print(f"thread {threading.current_thread().name} put {link}")
              self.queue.put(link)
      # write to file
      parsed = urlparse(url)
      filepath = construct_filepath(self.output_dir, parsed.netloc,
                                    parsed.path)
      with open(filepath, "w") as f:
        f.write(text)
    except Exception as e:
      print(f"Error fetching page {str(url)}: {str(e)}")

  def worker(self, max_pages: int):
    print(f"Starting worker {threading.current_thread().name}")
    num_pages = 0
    while True:
      try:
        url = self.queue.get(timeout=1)
      except queue.Empty:
        if self.finish_crawl.is_set():
          break
        continue
      print(f"Worker {threading.current_thread().name} is crawling {url}")
      with self.visited_lock:
        if len(self.visited_url) >= max_pages:
          print(f"Task done for {url} as max pages reached.")
          self.queue.task_done()
          if not self.finish_crawl.is_set():
            self.finish_crawl.set()
          ## NOTE: have to continue here, to continue to deque until the queue is empty
          continue
        if url in self.visited_url:
          print(f"Task done for {url} as already visited.")
          self.queue.task_done()
          continue
        self.visited_url.add(url)
      try:
        print(f"Worker {threading.current_thread().name} is parsing {url}")
        # extract domain
        parsed = urlparse(url)
        # check if robots.txt exists
        rp = RobotFileParser(
            urljoin(f"{parsed.scheme}://{parsed.netloc}", "robots.txt"))
        rp.read()
        if rp.can_fetch(self.agent, url):
          self.fetch_page(url)
        num_pages += 1
        print(f"task done for {url}")
      finally:
        self.queue.task_done()
    print(
        f"Worker {threading.current_thread().name} finished, downloaded {num_pages} pages."
    )

  def crawl(self):
    threads = []
    for i in range(self.num_workers):
      t = threading.Thread(target=self.worker, args=(self.max_pages, ))
      t.start()
      threads.append(t)
    self.queue.join()
    self.finish_crawl.set()
    print("All tasks are done")
    for t in threads:
      t.join(timeout=10)


def test_get_outbound_links():
  text = """
  <html>
    <head>
      <link rel="stylesheet" href="style.css">
    </head>
    <body>
      <a href="https://example.com">Example</a>
      <a href="https://example.com/page2">Page 2</a>
      <a href="page3">Page 3</a>
      <a href="https://def.com/page4">Page 4</a>
    </body>
  </html>
  """
  base_url = "https://example.com"
  outbound_links = get_outbound_links(text, base_url)
  assert outbound_links == {
      "https://example.com",
      "https://example.com/page2",
      "https://example.com/page3",
      "https://def.com/page4",
      "https://example.com/style.css",
  }

  outbound_links = get_outbound_links(text, "https://abc.com")
  assert outbound_links == {
      "https://example.com",
      "https://example.com/page2",
      "https://abc.com/page3",
      "https://def.com/page4",
      "https://abc.com/style.css",
  }
  print("All tests passed!")


def download():
  crawler = Crawler("https://chanderzuo.github.io",
                    0.1,
                    "output/chandlerzuo.github.io",
                    2,
                    num_workers=2)
  crawler.crawl()
  print("Results saved to chandlerzuo.github.io")


if __name__ == "__main__":
  # test_get_outbound_links()
  download()
