import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
from collections import deque
import logging
from utils import sanitize_filename, generate_metadata

# Configuration
START_URL = "https://www.icmr.gov.in/standard-treatment-workflows-stws"
DOMAIN = "icmr.gov.in"
DOWNLOAD_DIR = "data/downloads"
METADATA_DIR = "data/metadata"
MIN_FILE_SIZE = 50 * 1024  # 50 KB
MAX_PAGES = 1000  # Safety limit
TIMEOUT = 10
USER_AGENT = "ICMR_STW_Crawler/1.0"

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("crawler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ICMRCrawler:
    def __init__(self):
        self.visited = set()
        self.queue = deque([START_URL])
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        
        # Ensure directories exist
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        os.makedirs(METADATA_DIR, exist_ok=True)

    def is_valid_url(self, url):
        """Checks if URL is within the allowed domain and has a valid scheme."""
        parsed = urlparse(url)
        # Check scheme (http/https only)
        if parsed.scheme not in ("http", "https"):
            return False
            
        return parsed.netloc.endswith(DOMAIN) or parsed.netloc == ""

    def is_relevant_pdf(self, url):
        """
        Checks if the PDF URL is relevant for STW (Standard Treatment Workflows).
        Criterion: URL contains '/stws/' (case-insensitive) OR filename contains 'stw'.
        """
        url_lower = url.lower()
        if "/stws/" in url_lower:
            return True
            
        filename = os.path.basename(urlparse(url).path).lower()
        if "stw" in filename:
            return True
            
        return False

    def process_pdf(self, url):
        """Downloads PDF and generates metadata."""
        try:
            # Use GET with stream=True instead of HEAD to avoid 405 errors
            response = self.session.get(url, stream=True, timeout=TIMEOUT)
            if response.status_code != 200:
                logger.warning(f"Failed to access PDF: {url} (Status: {response.status_code})")
                response.close()
                return

            # Check content type
            content_type = response.headers.get("Content-Type", "").lower()
            if "application/pdf" not in content_type:
                logger.info(f"Skipping non-PDF content: {url} ({content_type})")
                response.close()
                return

            # STRICT FILTER: Check if it's an STW-related PDF
            if not self.is_relevant_pdf(url):
                logger.info(f"Skipping non-STW PDF: {url}")
                response.close()
                return

            # Check file size if available
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) < MIN_FILE_SIZE:
                logger.info(f"Skipping small PDF ({content_length} bytes): {url}")
                response.close()
                return

            # Download content
            logger.info(f"Downloading: {url}")
            content = b""
            for chunk in response.iter_content(chunk_size=8192):
                content += chunk
            
            if len(content) < MIN_FILE_SIZE:
                 logger.info(f"Skipping small PDF after download ({len(content)} bytes): {url}")
                 return

            # Save file
            filename = sanitize_filename(url)
            local_path = os.path.join(DOWNLOAD_DIR, filename)
            
            with open(local_path, "wb") as f:
                f.write(content)
            
            # Generate metadata
            generate_metadata(url, local_path, METADATA_DIR)
            logger.info(f"Saved: {filename}")

        except Exception as e:
            logger.error(f"Error processing PDF {url}: {e}")

    def crawl(self):
        pages_crawled = 0
        
        while self.queue and pages_crawled < MAX_PAGES:
            url = self.queue.popleft()
            # BFS leaf node handling
            if url.lower().endswith(".pdf"):
                if url not in self.visited:
                    self.visited.add(url)
                    self.process_pdf(url)
                continue

            
            if url in self.visited:
                continue
            
            self.visited.add(url)
            logger.info(f"Crawling: {url}")
            
            try:
                response = self.session.get(url, timeout=TIMEOUT)
                if response.status_code != 200:
                    logger.warning(f"Failed to fetch {url}: {response.status_code}")
                    continue

                content_type = response.headers.get("Content-Type", "").lower()
                
                # If it's a PDF (direct link case)
                if "application/pdf" in content_type:
                    self.process_pdf(url)
                    continue
                
                # If it's HTML, parse for links
                if "text/html" in content_type:
                    pages_crawled += 1
                    soup = BeautifulSoup(response.content, "html.parser")
                    
                    for link in soup.find_all("a", href=True):
                        href = link["href"].strip()
                        full_url = urljoin(url, href)
                        
                        # Normalize URL (remove fragments)
                        full_url = full_url.split("#")[0]
                        
                        if not self.is_valid_url(full_url):
                            continue
                        
                        # Identify potential PDFs
                        if full_url.lower().endswith(".pdf"):
                            if full_url not in self.visited:
                                self.queue.append(full_url)

                        
                        # Add HTML pages to queue
                        elif (
                           full_url not in self.visited and
                           (
                             "standard-treatment-workflows" in full_url or
                             "/stw" in full_url or
                             "/STWs/" in full_url or
                             "guidelines" in full_url
                           )
                        ):
                            self.queue.append(full_url)

                time.sleep(0.5) # Polite delay

            except Exception as e:
                logger.error(f"Error crawling {url}: {e}")

        logger.info("Crawling completed.")

if __name__ == "__main__":
    crawler = ICMRCrawler()
    crawler.crawl()
