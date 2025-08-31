import asyncio, re, urllib.parse, httpx
from bs4 import BeautifulSoup
from readability import Document   # makes content cleaner
import os, uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ---------------- URL Fetching ----------------
async def fetch_links(client, url, base_netloc):
    try:
        r = await client.get(url, timeout=10, follow_redirects=True)
        r.raise_for_status()
    except Exception as e:
        print(f"⚠️ Error fetching {url}: {e}")
        return []

    soup = BeautifulSoup(r.text, "lxml")
    new_links = []

    for a in soup.find_all("a", href=True):
        href = urllib.parse.urljoin(url, a["href"])
        hrefp = urllib.parse.urlparse(href)
        norm = urllib.parse.urlunparse((hrefp.scheme, hrefp.netloc, hrefp.path, "", "", ""))

        if hrefp.netloc != base_netloc:
            continue
        if re.search(r"\.(png|jpg|jpeg|gif|svg|zip|pdf|docx|xls|mp4)$", norm, re.I):
            continue

        new_links.append(norm)
    return new_links


async def discover_urls(start_url: str = None, max_urls: int = None, concurrency: int = None):
    # Get configuration from environment variables
    if start_url is None:
        start_url = os.getenv('SCRAPE_URL')
    if max_urls is None:
        max_urls = int(os.getenv('MAX_URLS', '1000'))
    if concurrency is None:
        concurrency = int(os.getenv('CONCURRENCY', '10'))
    parsed = urllib.parse.urlparse(start_url)
    base_netloc = parsed.netloc

    seen = set([start_url])
    queue = [start_url]

    async with httpx.AsyncClient() as client:
        while queue and len(seen) < max_urls:
            batch, queue = queue[:concurrency], queue[concurrency:]
            tasks = [fetch_links(client, url, base_netloc) for url in batch]
            results = await asyncio.gather(*tasks)

            for new_links in results:
                for link in new_links:
                    if link not in seen:
                        seen.add(link)
                        queue.append(link)

            print(f"Discovered so far: {len(seen)} URLs")

    print(f"\n🔎 Found total {len(seen)} unique URLs")
    return list(seen)


# ---------------- Page Scraping ----------------
async def scrape_page(client, url):
    """Download + clean main content from a URL"""
    try:
        r = await client.get(url, timeout=10, follow_redirects=True)
        r.raise_for_status()
    except Exception as e:
        print(f"❌ Failed {url}: {e}")
        return None

    doc = Document(r.text)
    title = doc.short_title()
    html_content = doc.summary()  # always returns HTML
    soup = BeautifulSoup(html_content, "lxml")
    content = soup.get_text(separator="\n", strip=True)  # convert to plain text

    text = f"{title}\n\n{content}".strip()
    print(f"✅ Scraped {url} | {len(text)} chars")
    return {"url": url, "title": title, "content": text}


async def scrape_all(urls, concurrency: int = None):
    if concurrency is None:
        concurrency = int(os.getenv('CONCURRENCY', '10'))
    scraped = []
    async with httpx.AsyncClient() as client:
        for i in range(0, len(urls), concurrency):
            batch = urls[i:i+concurrency]
            tasks = [scrape_page(client, u) for u in batch]
            results = await asyncio.gather(*tasks)
            scraped.extend([r for r in results if r])
    return scraped


# ---------------- Main ----------------
if __name__ == "__main__":
    # Get configuration from environment variables
    start_url = os.getenv('SCRAPE_URL')
    max_urls = int(os.getenv('MAX_URLS', '1000'))
    scraped_pages_dir = os.getenv('SCRAPED_PAGES_DIR', './scraped_pages')
    
    if not start_url:
        print("❌ Error: SCRAPE_URL not found in environment variables")
        print("Please set SCRAPE_URL in your .env file")
        exit(1)
    
    print(f"🔎 Starting scrape of: {start_url}")
    print(f"📊 Max URLs: {max_urls}")
    
    urls = asyncio.run(discover_urls(start_url, max_urls))
    scraped_data = asyncio.run(scrape_all(urls))

    # Save to local txt files (or directly to DB)
    os.makedirs(scraped_pages_dir, exist_ok=True)
    for item in scraped_data:
        fname = f"{scraped_pages_dir}/{uuid.uuid4().hex}.txt"
        with open(fname, "w", encoding="utf-8") as f:
            f.write(item["content"])

    print(f"\n📂 Saved {len(scraped_data)} pages into {scraped_pages_dir}/")