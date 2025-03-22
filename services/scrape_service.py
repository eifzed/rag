from schemas.scrap_schema import ScrapingResponse
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import asyncio
from typing import List, Dict
from fastapi import HTTPException


class ScrapeService:
    @staticmethod
    async def fetch_url(url: str, client: httpx.AsyncClient) -> str:
        try:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
            return response.text
        except httpx.HTTPError as e:
            raise HTTPException(status_code=400, detail=f"Error fetching URL: {str(e)}")
    
    @staticmethod
    async def scrape_url_with_depth(url: str, depth: int) -> ScrapingResponse:
        async with httpx.AsyncClient(timeout=30.0) as client:
            html = await ScrapeService.fetch_url(url, client)
            content = ScrapeService._extract_main_content(html, url)
            
            result = ScrapingResponse(url=url, content=content)
            
            if depth > 1:
                important_links = ScrapeService._extract_important_links(html, url)
                result.links = []
                
                # Limit concurrent requests
                tasks = []
                for link_info in important_links:
                    link_url = link_info["url"]
                    tasks.append(ScrapeService.fetch_url(link_url, client))
                
                html_contents = await asyncio.gather(*tasks, return_exceptions=True)
                
                for i, html_content in enumerate(html_contents):
                    if isinstance(html_content, Exception):
                        # Handle failed requests
                        result.links.append({
                            "url": important_links[i]["url"],
                            "text": important_links[i]["text"],
                            "content": f"Error fetching content: {str(html_content)}",
                        })
                    else:
                        # Extract content from successful requests
                        link_content = ScrapeService._extract_main_content(html_content, important_links[i]["url"])
                        result.links.append({
                            "url": important_links[i]["url"],
                            "text": important_links[i]["text"],
                            "content": link_content,
                        })
            
            return result
    
    @staticmethod
    def _extract_main_content(html: str, url: str = "") -> str:
        """Extract the main content from HTML, with special handling for known sites."""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Special handling for Indonesian news sites
        if "kompas.com" in url.lower():
            return ScrapeService._extract_kompas_content(soup)
        elif "detik.com" in url.lower():
            return ScrapeService._extract_detik_content(soup)
        elif "tribunnews.com" in url.lower():
            return ScrapeService._extract_tribun_content(soup)
        elif "tempo.co" in url.lower():
            return ScrapeService._extract_tempo_content(soup)
        
        # Remove unnecessary elements
        for element in soup.find_all(['nav', 'header', 'footer', 'script', 'style', 'aside']):
            element.decompose()
        
        # Try to find main content container
        main_content = None
        for container in ['main', 'article', '.content', '#content', '.post', '.article', '[itemprop="articleBody"]']:
            if container.startswith('.') or container.startswith('#') or container.startswith('['):
                main_content = soup.select_one(container)
            else:
                main_content = soup.find(container)
            if main_content:
                break
        
        # If no specific content container found, use body
        if not main_content:
            main_content = soup.body
        
        # Further clean the content
        if main_content:
            # Remove ads, related articles, share buttons, etc.
            for selector in ['.ads', '.advertisement', '.share', '.related', '.recommended', '.social', 
                           '.comments', '.navigation', '.pagination', '.tags']:
                for element in main_content.select(selector):
                    element.decompose()
                    
            # Extract text with paragraph separation
            paragraphs = main_content.find_all('p')
            if paragraphs:
                content = "\n\n".join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
            else:
                content = re.sub(r'\s+', ' ', main_content.get_text())
                
            return content.strip()
        
        return ""
    
    @staticmethod
    def _extract_kompas_content(soup):
        """Extract content specifically from Kompas.com articles."""
        article_content = ""
        
        # Get article title
        title = soup.select_one('h1.read__title')
        if title:
            article_content += title.get_text().strip() + "\n\n"
        
        # Get article date
        date = soup.select_one('.read__time')
        if date:
            article_content += date.get_text().strip() + "\n\n"
        
        # Get article author
        author = soup.select_one('.read__author__name')
        if author:
            article_content += "Penulis: " + author.get_text().strip() + "\n\n"
        
        # Get article content
        main_content = soup.select_one('.read__content')
        
        # If we can't find the specific Kompas content container, try general article containers
        if not main_content:
            main_content = soup.select_one('article') or soup.select_one('.article-content')
        
        if main_content:
            # Remove interactive elements, ads, etc.
            for element in main_content.select('.ads, .advertisement, .widget, .related, .social-share, .read__bacajuga, .read__terpopuler, .lihat-juga'):
                element.decompose()
            
            # Get paragraphs
            paragraphs = main_content.find_all('p')
            if paragraphs:
                article_content += "\n\n".join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
        
        # If we still couldn't extract content, try a more general approach
        if not article_content:
            # Look for the text starting with city name and Kompas.com
            # This is a common pattern in Kompas articles: "JAKARTA, KOMPAS.com - ..."
            body_text = soup.get_text()
            city_pattern = r'([A-Z]+, KOMPAS\.com.+?)(?:Terpopuler|Trending|Pilihan Untukmu|Lihat Semua)'
            match = re.search(city_pattern, body_text, re.DOTALL)
            if match:
                article_content = match.group(1).strip()
        
        return article_content
    
    @staticmethod
    def _extract_detik_content(soup):
        """Extract content specifically from Detik.com articles."""
        article_content = ""
        
        # Get article title
        title = soup.select_one('h1.detail__title')
        if title:
            article_content += title.get_text().strip() + "\n\n"
        
        # Get article date
        date = soup.select_one('.detail__date')
        if date:
            article_content += date.get_text().strip() + "\n\n"
        
        # Get article content
        main_content = soup.select_one('.detail__body-text')
        
        if main_content:
            # Remove unwanted elements
            for element in main_content.select('.ads, .advertisement, .related-article'):
                element.decompose()
                
            # Get paragraphs
            paragraphs = main_content.find_all('p')
            if paragraphs:
                article_content += "\n\n".join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
        
        return article_content
    
    @staticmethod
    def _extract_tribun_content(soup):
        """Extract content specifically from Tribunnews.com articles."""
        article_content = ""
        
        # Get article title
        title = soup.select_one('h1.f50')
        if title:
            article_content += title.get_text().strip() + "\n\n"
        
        # Get article content
        main_content = soup.select_one('.side-article.txt-article')
        
        if main_content:
            # Remove unwanted elements
            for element in main_content.select('.ads, .advertisement, .related'):
                element.decompose()
                
            # Get paragraphs
            paragraphs = main_content.find_all('p')
            if paragraphs:
                article_content += "\n\n".join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
        
        return article_content
    
    @staticmethod
    def _extract_tempo_content(soup):
        """Extract content specifically from Tempo.co articles."""
        article_content = ""
        
        # Get article title
        title = soup.select_one('h1.title')
        if title:
            article_content += title.get_text().strip() + "\n\n"
        
        # Get article date
        date = soup.select_one('.article__date')
        if date:
            article_content += date.get_text().strip() + "\n\n"
        
        # Get article content
        main_content = soup.select_one('.detail-in')
        
        if main_content:
            # Remove unwanted elements
            for element in main_content.select('.ads, .advertisement, .related-articles'):
                element.decompose()
                
            # Get paragraphs
            paragraphs = main_content.find_all('p')
            if paragraphs:
                article_content += "\n\n".join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
        
        return article_content
    
    @staticmethod
    def _extract_important_links(html: str, base_url: str) -> List[Dict[str, str]]:
        """Extract important links from HTML content."""
        soup = BeautifulSoup(html, 'html.parser')
        important_links = []
        base_domain = urlparse(base_url).netloc
        
        # For Indonesian news sites, prioritize certain types of links
        is_indonesian_news = any(site in base_url.lower() for site in ["kompas.com", "detik.com", "tribunnews.com", "tempo.co"])
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag.get('href')
            if not href:
                continue
            
            # Resolve relative URLs
            full_url = urljoin(base_url, href)
            parsed_url = urlparse(full_url)
            
            # Exclude fragment links, query parameters, and non-http(s) links
            if (not parsed_url.scheme.startswith('http') or 
                not parsed_url.netloc or 
                parsed_url.path.endswith(('.jpg', '.jpeg', '.png', '.gif', '.css', '.js'))):
                continue
            
            link_text = a_tag.get_text().strip()
            is_internal = parsed_url.netloc == base_domain
            
            # Check if link is in main content area
            is_in_content = False
            parent = a_tag.find_parent(['main', 'article', 'section', 'div.content', 'div#content'])
            if parent:
                is_in_content = True
            
            # Score the importance of the link
            importance_score = 0
            if is_internal:
                importance_score += 2
            if len(link_text) > 10:
                importance_score += 1
            if is_in_content:
                importance_score += 2
                
            # Special handling for Indonesian news sites
            if is_indonesian_news:
                # Prioritize links to other news articles (often have date patterns in URL)
                if re.search(r'/\d{4}/\d{2}/\d{2}/', full_url):
                    importance_score += 3
                
                # Deprioritize category pages, tag pages, author pages
                if any(x in full_url.lower() for x in ['/tag/', '/category/', '/author/', '/indeks/', '/video/']):
                    importance_score -= 2
            
            # Skip links with low importance
            if importance_score >= 3:
                important_links.append({
                    "url": full_url,
                    "text": link_text,
                    "importance": importance_score
                })
        
        # Sort by importance and return top links (limit to 5)
        important_links.sort(key=lambda x: x["importance"], reverse=True)
        return important_links[:5]