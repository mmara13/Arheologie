import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin, urlparse
import re
from datetime import datetime

def get_article_data(url):
    """Extrage textul, titlul și data unui articol."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extrage titlul
            title = None
            title_tag = (
                soup.find('h1') or 
                soup.find('title') or 
                soup.find(class_=re.compile(r'title|headline', re.I))
            )
            if title_tag:
                title = title_tag.get_text().strip()
            
            # Extrage data
            date = None
            # Caută data în meta tags
            meta_date = (
                soup.find('meta', property='article:published_time') or
                soup.find('meta', property='og:published_time') or
                soup.find('meta', itemprop='datePublished')
            )
            if meta_date:
                date = meta_date.get('content')
            else:
                # Caută data în elemente HTML
                date_patterns = [
                    r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
                    r'\d{2}\.\d{2}\.\d{4}', # DD.MM.YYYY
                    r'\d{2}/\d{2}/\d{4}'    # DD/MM/YYYY
                ]
                for element in soup.find_all(['time', 'span', 'div']):
                    text = element.get_text().strip()
                    for pattern in date_patterns:
                        match = re.search(pattern, text)
                        if match:
                            date = match.group()
                            break
                    if date:
                        break
            
            # Extrage conținutul
            for element in soup.find_all(['nav', 'header', 'footer', 'aside']):
                element.decompose()
                
            article_container = soup.find('article') or soup.find('div', class_='article-content')
            
            if article_container:
                paragraphs = article_container.find_all('p')
            else:
                paragraphs = soup.find_all('p')
            
            text = ' '.join(para.get_text().strip() for para in paragraphs if para.get_text().strip())
            
            if len(text) > 100:
                return {
                    'content': text,
                    'title': title or 'No title found',
                    'date': date or 'No date found'
                }
        return None
    except Exception as e:
        print(f"Error fetching article {url}: {e}")
        return None

def is_valid_article_link(url, link, site_url):
    """Verifică dacă un link este valid pentru scraping."""
    invalid_patterns = ['#', 'javascript:', 'mailto:', '/tag/', '/author/', '/category/', '/search/', '/contact/', '/about/']
    if any(pattern in url.lower() for pattern in invalid_patterns):
        return False
        
    if not url.startswith(('http://', 'https://')):
        url = urljoin(site_url, url)
    return site_url in url

def get_pagination_urls(base_url):
    """Extrage URL-urile pentru paginare."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(base_url, headers=headers, timeout=10)
        if response.status_code != 200:
            return [base_url]

        soup = BeautifulSoup(response.content, 'html.parser')
        parsed_url = urlparse(base_url)
        domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        pagination_links = set()
        pagination_links.add(base_url)
        
        page_patterns = [
            r'page/\d+', r'pag(e|ina)/\d+', r'p=\d+', r'page=\d+',
            r'/\d+$', r'pag/\d+', r'pagina/\d+'
        ]
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            if not href.startswith(('http://', 'https://')):
                href = urljoin(domain, href)
                
            if any(re.search(pattern, href) for pattern in page_patterns):
                pagination_links.add(href)
                
        pagination_links = sorted(list(pagination_links))[:10]
        
        return pagination_links if pagination_links else [base_url]
    except Exception as e:
        print(f"Error getting pagination for {base_url}: {e}")
        return [base_url]

def scrape_articles(site, max_articles=200, start_index=50000):
    """Extrage linkurile articolelor și salvează textul acestora."""
    try:
        pagination_urls = get_pagination_urls(site['url'])
        print(f"Found {len(pagination_urls)} pages for {site['url']}")
        
        all_article_links = set()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        for page_url in pagination_urls:
            try:
                response = requests.get(page_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    for nav in soup.find_all(['nav', 'header', 'footer']):
                        nav.decompose()
                    
                    main_content = soup.find('main') or soup.find('div', class_='content')
                    links = main_content.find_all('a', href=True) if main_content else soup.find_all('a', href=True)
                    
                    for link in links:
                        href = link['href']
                        if is_valid_article_link(href, link, site['url']):
                            full_url = urljoin(site['url'], href)
                            all_article_links.add(full_url)
                            if len(all_article_links) >= max_articles:
                                break
                    
                    if len(all_article_links) >= max_articles:
                        break
                        
            except Exception as e:
                print(f"Error processing page {page_url}: {e}")
                continue
        
        os.makedirs(f"stiri_siteuri/{site['label']}", exist_ok=True)
        saved_count = 0
        current_index = start_index
        
        for article_url in all_article_links:
            if saved_count >= max_articles:
                break
                
            article_data = get_article_data(article_url)
            if article_data:
                # Salvează conținutul
                content_file = f"stiri_siteuri/{site['label']}/{current_index}.txt"
                with open(content_file, "w", encoding="utf-8") as f:
                    f.write(article_data['content'])
                
                # Salvează titlul și data
                title_file = f"stiri_siteuri/{site['label']}/t{current_index}.txt"
                with open(title_file, "w", encoding="utf-8") as f:
                    f.write(f"{article_data['title']}\n{article_data['date']}")
                
                print(f"Saved article {saved_count + 1}: {content_file} and {title_file}")
                saved_count += 1
                current_index += 1
        
        print(f"Finished scraping {site['url']}. Saved {saved_count} articles from {len(pagination_urls)} pages.")
        return current_index
    except Exception as e:
        print(f"Error scraping site {site['url']}: {e}")
        return start_index

# Lista site-urilor
url_list = [
    {'url': 'https://www.digi24.ro', 'label': 'ro_digi'},
    {'url': 'https://zugo.md/toate-stirile', 'label': 'md_zugo'},
    {'url': 'https://life.ro/', 'label': 'ro_life'},
    {'url': 'https://anticoruptie.md/', 'label': 'md_anticoruptie'},
    {'url': 'https://pressone.ro/', 'label': 'ro_pressone'},
    {'url': 'https://hotnews.ro/', 'label': 'ro_hotnews'},
     {'url': 'https://www.noi.md', 'label': 'md_noi'},
    {'url': 'https://www.zdg.md', 'label': 'md_zdg'},
    {'url': 'https://www.agora.md', 'label': 'md_agora'},
    {'url': 'https://www.bani.md', 'label': 'md_bani'},
    {'url': 'https://www.ea.md', 'label': 'md_ea'},
{'url': 'https://www.digi24.ro/stiri/externe/moldova', 'label': 'md_digi'},
]# Începe de la indexul inițial și continuă numerotarea
current_index = 50000
for site in url_list:
    current_index = scrape_articles(site, start_index=current_index)