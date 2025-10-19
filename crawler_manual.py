from bs4 import BeautifulSoup
from typing import Set, Optional
from urllib.parse import urljoin, urldefrag, urlparse
from urllib.robotparser import RobotFileParser
import requests
from collections import deque
import os
import time


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
               max_pages: int):
    self.seed_url = seed_url
    self.session = requests.Session()
    self.visited_url: Set[str] = set()
    self.queue = deque([seed_url])
    self.max_pages = max_pages
    self.output_dir = output_dir
    if not os.path.exists(output_dir):
      os.makedirs(output_dir)
    self.agent = "WebCrawler/1.0 Educational Purpose"
    self.delay = delay

  def fetch_page(self, url: str):
    outbound_links: Set[str] = set()
    try:
      response = self.session.get(url, timeout=10, allow_redirects=True)
      text = response.text
      outbound_links = get_outbound_links(text, url)
      outbound_links = outbound_links - self.visited_url
      self.queue.extend(outbound_links)
      # write to file
      parsed = urlparse(url)
      filepath = construct_filepath(self.output_dir, parsed.netloc, parsed.path)
      with open(filepath, "w") as f:
        print(f"Writing {url} to file")
        f.write(text)
    except Exception as e:
      print(f"Error fetching page {str(url)}: {str(e)}")

  def crawl(self):
    while self.queue and len(self.visited_url) < self.max_pages:
      url = self.queue.popleft()
      self.visited_url.add(url)
      # extract domain
      parsed = urlparse(url)
      # check if robots.txt exists
      rp = RobotFileParser(
          urljoin(f"{parsed.scheme}://{parsed.netloc}", "robots.txt"))
      rp.read()
      if rp.can_fetch(self.agent, url):
        get_outbound_links = self.fetch_page(url)
        time.sleep(self.delay)


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
  crawler = Crawler("https://chanderzuo.github.io", 0.1,
                    "output/chandlerzuo.github.io", 10)
  crawler.crawl()
  print("Results saved to chandlerzuo.github.io")


if __name__ == "__main__":
  # test_get_outbound_links()
  download()
