import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from whoosh.fields import Schema, TEXT, ID
from whoosh.index import create_in
import os

# Function to crawl pages
def crawl(start_url, max_depth=2):
    visited = set()  # Keep track of visited URLs
    to_visit = [(start_url, 0)]  # List of (URL, depth)
    pages = {}  # Store crawled pages

    while to_visit:
        url, depth = to_visit.pop(0)
        if url in visited or depth > max_depth:
            continue
        try:
            response = requests.get(url, timeout=5)
            if 'text/html' not in response.headers.get('Content-Type', ''):
                continue
            soup = BeautifulSoup(response.text, 'html.parser')
            visited.add(url)
            pages[url] = soup.get_text()  # Extract text content
            # Debug: Log crawled URL and content preview
            print(f"Crawled URL: {url}")
            print(f"Content sample: {pages[url][:200]}...")
            # Find all links and add them to the queue
            for link in soup.find_all('a', href=True):
                full_url = urljoin(url, link['href'])
                if full_url not in visited:
                    to_visit.append((full_url, depth + 1))
        except Exception as e:
            print(f"Error crawling {url}: {e}")
    return pages

# Function to build the Whoosh index
def build_whoosh_index(pages, index_dir="index"):
    # Define the schema for the Whoosh index
    schema = Schema(
    title=TEXT(stored=True),
    content=TEXT(stored=True),  # Ensure content is stored
    url=ID(stored=True)
)


    # Create the index directory if it doesn't exist
    if not os.path.exists(index_dir):
        os.mkdir(index_dir)

    # Create the Whoosh index
    ix = create_in(index_dir, schema)
    writer = ix.writer()

    # Add documents to the index
    for url, content in pages.items():
        # Debug: Log each document being added
        print(f"Indexing content for URL: {url}")
        print(f"Content sample: {content[:200]}...")
        writer.add_document(
            title=url.split("/")[-1],  # Use the last part of the URL as the title
            content=content,
            url=url
        )
    writer.commit()
    print("Whoosh index built successfully!")

# Main block to test the functionality
if __name__ == "__main__":
    # Start crawling from the given URL
    start_url = "https://vm009.rz.uos.de/crawl/index.html"
    pages = crawl(start_url)
    print(f"Crawled {len(pages)} pages.")
    
    # Build the Whoosh index
    build_whoosh_index(pages)
