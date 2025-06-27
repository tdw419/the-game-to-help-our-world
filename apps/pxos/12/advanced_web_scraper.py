#!/usr/bin/env python3
"""
Advanced Web Scraper - Comprehensive web data extraction for PXBot
"""

import os
import json
import urllib.request
import urllib.parse
import html
import re
import time
from datetime import datetime
import threading

class AdvancedWebScraper:
    def __init__(self, pxbot_instance=None):
        self.name = "Advanced Web Scraper"
        self.version = "1.2.0"
        self.description = "Comprehensive web data extraction and analysis"
        self.pxbot = pxbot_instance
        
        # Scraper state
        self.scraped_data = {}
        self.scraping_history = []
        self.scraped_apis = {}
        self.config = self.load_config()
        
        # HTTP headers for requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Load persistent data
        self.load_history()
    
    def load_config(self):
        """Load scraper configuration"""
        config_path = os.path.join("pxbot_code", "webscraper_config.json")
        default_config = {
            "timeout": 10,
            "max_retries": 3,
            "delay_between_requests": 1.0,
            "max_content_length": 1000000,  # 1MB
            "auto_save_data": True,
            "extract_links": True,
            "extract_images": True,
            "extract_emails": True,
            "respect_robots_txt": True
        }
        
        try:
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
        except Exception as e:
            print(f"Config load error: {e}")
        
        return default_config
    
    def save_config(self):
        """Save scraper configuration"""
        config_path = os.path.join("pxbot_code", "webscraper_config.json")
        try:
            os.makedirs("pxbot_code", exist_ok=True)
            with open(config_path, "w") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Config save error: {e}")
    
    def load_history(self):
        """Load scraping history"""
        history_path = os.path.join("pxbot_code", "scraping_history.json")
        try:
            if os.path.exists(history_path):
                with open(history_path, "r") as f:
                    self.scraping_history = json.load(f)[-100:]  # Keep last 100 entries
        except Exception as e:
            print(f"History load error: {e}")
    
    def save_history(self):
        """Save scraping history"""
        if not self.config.get("auto_save_data", True):
            return
        
        history_path = os.path.join("pxbot_code", "scraping_history.json")
        try:
            os.makedirs("pxbot_code", exist_ok=True)
            with open(history_path, "w") as f:
                json.dump(self.scraping_history[-100:], f, indent=2)
        except Exception as e:
            print(f"History save error: {e}")
    
    def execute_command(self, command):
        """Main command handler"""
        try:
            if command.startswith("scrape:"):
                cmd = command[7:]
                return self.handle_scraper_command(cmd)
            else:
                return "Use scrape: prefix for web scraper commands"
        except Exception as e:
            return f"Error: {e}"
    
    def handle_scraper_command(self, command):
        """Handle scraper-specific commands"""
        parts = command.split(":", 1)
        action = parts[0]
        
        try:
            if action == "url":
                url = parts[1] if len(parts) > 1 else ""
                return self.scrape_url(url)
            
            elif action == "bulk":
                urls_str = parts[1] if len(parts) > 1 else ""
                return self.scrape_bulk_urls(urls_str)
            
            elif action == "github":
                repo = parts[1] if len(parts) > 1 else ""
                return self.scrape_github_repo(repo)
            
            elif action == "api":
                api_url = parts[1] if len(parts) > 1 else ""
                return self.scrape_api(api_url)
            
            elif action == "news":
                topic = parts[1] if len(parts) > 1 else "technology"
                return self.scrape_news(topic)
            
            elif action == "search":
                if len(parts) > 1:
                    search_parts = parts[1].split(":", 1)
                    engine = search_parts[0]
                    query = search_parts[1] if len(search_parts) > 1 else ""
                    return self.search_web(engine, query)
                return "Usage: scrape:search:engine:query"
            
            elif action == "analyze":
                key = parts[1] if len(parts) > 1 else ""
                return self.analyze_scraped_data(key)
            
            elif action == "extract":
                if len(parts) > 1:
                    extract_parts = parts[1].split(":", 1)
                    data_type = extract_parts[0]
                    key = extract_parts[1] if len(extract_parts) > 1 else ""
                    return self.extract_data(data_type, key)
                return "Usage: scrape:extract:type:key"
            
            elif action == "export":
                name = parts[1] if len(parts) > 1 else "scraped_data"
                return self.export_to_pxbot(name)
            
            elif action == "list":
                filter_type = parts[1] if len(parts) > 1 else "all"
                return self.list_scraped_data(filter_type)
            
            elif action == "history":
                count = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 10
                return self.show_history(count)
            
            elif action == "clear":
                data_type = parts[1] if len(parts) > 1 else "data"
                return self.clear_data(data_type)
            
            elif action == "config":
                if len(parts) > 1:
                    config_cmd = parts[1]
                    return self.handle_config(config_cmd)
                else:
                    return self.show_config()
            
            elif action == "stats":
                return self.show_statistics()
            
            else:
                return self.show_help()
                
        except Exception as e:
            return f"Command error: {e}"
    
    def scrape_url(self, url):
        """Scrape a single URL"""
        if not url.strip():
            return "❌ Please provide a URL to scrape"
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        try:
            # Add delay between requests
            if self.scraping_history:
                time.sleep(self.config.get("delay_between_requests", 1.0))
            
            req = urllib.request.Request(url, headers=self.headers)
            
            with urllib.request.urlopen(req, timeout=self.config.get("timeout", 10)) as response:
                # Check content length
                content_length = response.headers.get('Content-Length')
                if content_length and int(content_length) > self.config.get("max_content_length", 1000000):
                    return f"❌ Content too large: {content_length} bytes"
                
                content = response.read()
                
                # Try to decode content
                try:
                    if hasattr(response, 'headers'):
                        charset = response.headers.get_content_charset()
                        if charset:
                            html_content = content.decode(charset)
                        else:
                            html_content = content.decode('utf-8')
                    else:
                        html_content = content.decode('utf-8')
                except:
                    html_content = content.decode('utf-8', errors='ignore')
                
                # Extract and process data
                extracted_data = self.process_html_content(html_content, url)
                
                # Store scraped data
                timestamp = datetime.now().isoformat()
                self.scraped_data[url] = {
                    'timestamp': timestamp,
                    'url': url,
                    'content_length': len(html_content),
                    'text_content': extracted_data['text'],
                    'title': extracted_data['title'],
                    'links': extracted_data['links'],
                    'images': extracted_data['images'],
                    'emails': extracted_data['emails'],
                    'metadata': extracted_data['metadata']
                }
                
                # Add to history
                self.scraping_history.append({
                    'url': url,
                    'timestamp': timestamp,
                    'success': True,
                    'data_size': len(extracted_data['text'])
                })
                
                # Auto-save
                if self.config.get("auto_save_data", True):
                    self.save_history()
                
                return f"✅ **Scraped successfully:** {url}\n\n**📊 Summary:**\n• Title: {extracted_data['title']}\n• Text length: {len(extracted_data['text'])} chars\n• Links found: {len(extracted_data['links'])}\n• Images found: {len(extracted_data['images'])}\n• Emails found: {len(extracted_data['emails'])}"
                
        except urllib.error.HTTPError as e:
            error_msg = f"❌ HTTP Error {e.code}: {e.reason}"
            self.scraping_history.append({
                'url': url,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': error_msg
            })
            return error_msg
        except urllib.error.URLError as e:
            error_msg = f"❌ URL Error: {e.reason}"
            self.scraping_history.append({
                'url': url,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': error_msg
            })
            return error_msg
        except Exception as e:
            error_msg = f"❌ Scraping error: {str(e)}"
            self.scraping_history.append({
                'url': url,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': error_msg
            })
            return error_msg
    
    def process_html_content(self, html_content, url):
        """Process and extract data from HTML content"""
        extracted = {
            'text': '',
            'title': '',
            'links': [],
            'images': [],
            'emails': [],
            'metadata': {}
        }
        
        try:
            # Extract title
            title_match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
            if title_match:
                extracted['title'] = html.unescape(title_match.group(1).strip())
            
            # Extract meta tags
            meta_matches = re.findall(r'<meta[^>]+>', html_content, re.IGNORECASE)
            for meta in meta_matches:
                name_match = re.search(r'name=["\']([^"\']+)["\']', meta, re.IGNORECASE)
                content_match = re.search(r'content=["\']([^"\']+)["\']', meta, re.IGNORECASE)
                if name_match and content_match:
                    extracted['metadata'][name_match.group(1)] = html.unescape(content_match.group(1))
            
            # Extract links if enabled
            if self.config.get("extract_links", True):
                link_matches = re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html_content, re.IGNORECASE | re.DOTALL)
                for href, text in link_matches:
                    # Convert relative URLs to absolute
                    if href.startswith('//'):
                        href = 'https:' + href
                    elif href.startswith('/'):
                        from urllib.parse import urljoin
                        href = urljoin(url, href)
                    elif not href.startswith(('http://', 'https://')):
                        continue
                    
                    extracted['links'].append({
                        'url': href,
                        'text': html.unescape(re.sub(r'<[^>]+>', '', text).strip())
                    })
            
            # Extract images if enabled
            if self.config.get("extract_images", True):
                img_matches = re.findall(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>', html_content, re.IGNORECASE)
                for img_src in img_matches:
                    # Convert relative URLs to absolute
                    if img_src.startswith('//'):
                        img_src = 'https:' + img_src
                    elif img_src.startswith('/'):
                        from urllib.parse import urljoin
                        img_src = urljoin(url, img_src)
                    extracted['images'].append(img_src)
            
            # Extract emails if enabled
            if self.config.get("extract_emails", True):
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                emails = re.findall(email_pattern, html_content)
                extracted['emails'] = list(set(emails))  # Remove duplicates
            
            # Extract text content
            extracted['text'] = self.html_to_text(html_content)
            
        except Exception as e:
            print(f"HTML processing error: {e}")
        
        return extracted
    
    def html_to_text(self, html_content):
        """Convert HTML to readable text"""
        try:
            # Remove script and style elements
            html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            
            # Convert common HTML elements to text
            html_content = re.sub(r'<br[^>]*>', '\n', html_content, flags=re.IGNORECASE)
            html_content = re.sub(r'<p[^>]*>', '\n\n', html_content, flags=re.IGNORECASE)
            html_content = re.sub(r'</p>', '', html_content, flags=re.IGNORECASE)
            html_content = re.sub(r'<h[1-6][^>]*>', '\n\n### ', html_content, flags=re.IGNORECASE)
            html_content = re.sub(r'</h[1-6]>', '\n', html_content, flags=re.IGNORECASE)
            html_content = re.sub(r'<li[^>]*>', '\n• ', html_content, flags=re.IGNORECASE)
            html_content = re.sub(r'</li>', '', html_content, flags=re.IGNORECASE)
            
            # Remove all other HTML tags
            html_content = re.sub(r'<[^>]+>', '', html_content)
            
            # Decode HTML entities
            html_content = html.unescape(html_content)
            
            # Clean up whitespace
            html_content = re.sub(r'\n\s*\n\s*\n', '\n\n', html_content)
            html_content = re.sub(r'[ \t]+', ' ', html_content)
            
            return html_content.strip()
        except:
            return "Error parsing HTML content"
    
    def scrape_bulk_urls(self, urls_str):
        """Scrape multiple URLs"""
        if not urls_str.strip():
            return "❌ Please provide URLs separated by commas or spaces"
        
        # Parse URLs
        urls = []
        for url in re.split(r'[,\s]+', urls_str):
            url = url.strip()
            if url:
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                urls.append(url)
        
        if not urls:
            return "❌ No valid URLs found"
        
        if len(urls) > 10:
            return "❌ Maximum 10 URLs allowed for bulk scraping"
        
        results = []
        successful = 0
        failed = 0
        
        for i, url in enumerate(urls, 1):
            result = self.scrape_url(url)
            if "✅" in result:
                successful += 1
                results.append(f"{i}. ✅ {url}")
            else:
                failed += 1
                results.append(f"{i}. ❌ {url} - {result.split(':', 1)[-1].strip()}")
        
        summary = f"📊 **Bulk Scraping Complete**\n\n**Results:** {successful} successful, {failed} failed\n\n"
        summary += "\n".join(results)
        
        return summary
    
    def scrape_github_repo(self, repo):
        """Scrape GitHub repository information"""
        if not repo or '/' not in repo:
            return "❌ Please provide a GitHub repo in format: user/repository"
        
        api_url = f"https://api.github.com/repos/{repo}"
        
        try:
            req = urllib.request.Request(api_url, headers=self.headers)
            
            with urllib.request.urlopen(req, timeout=self.config.get("timeout", 10)) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                # Also get README if available
                readme_url = f"https://api.github.com/repos/{repo}/readme"
                readme_content = ""
                try:
                    readme_req = urllib.request.Request(readme_url, headers=self.headers)
                    with urllib.request.urlopen(readme_req, timeout=5) as readme_response:
                        readme_data = json.loads(readme_response.read().decode('utf-8'))
                        if readme_data.get('content'):
                            import base64
                            readme_content = base64.b64decode(readme_data['content']).decode('utf-8')
                except:
                    pass
                
                repo_info = {
                    'name': data.get('name', 'Unknown'),
                    'full_name': data.get('full_name', repo),
                    'description': data.get('description', 'No description'),
                    'language': data.get('language', 'Unknown'),
                    'stars': data.get('stargazers_count', 0),
                    'forks': data.get('forks_count', 0),
                    'watchers': data.get('watchers_count', 0),
                    'issues': data.get('open_issues_count', 0),
                    'size': data.get('size', 0),
                    'url': data.get('html_url', ''),
                    'clone_url': data.get('clone_url', ''),
                    'created': data.get('created_at', ''),
                    'updated': data.get('updated_at', ''),
                    'pushed': data.get('pushed_at', ''),
                    'license': data.get('license', {}).get('name', 'None') if data.get('license') else 'None',
                    'topics': data.get('topics', []),
                    'readme': readme_content[:1000] + '...' if len(readme_content) > 1000 else readme_content
                }
                
                self.scraped_data[f"github:{repo}"] = {
                    'timestamp': datetime.now().isoformat(),
                    'type': 'github_repo',
                    'data': repo_info
                }
                
                # Add to history
                self.scraping_history.append({
                    'url': f"github:{repo}",
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'type': 'github_repo'
                })
                
                report = f"📦 **GitHub Repository: {repo_info['name']}**\n\n"
                report += f"**Description:** {repo_info['description']}\n"
                report += f"**Language:** {repo_info['language']}\n"
                report += f"**Stars:** {repo_info['stars']} ⭐ | **Forks:** {repo_info['forks']} 🍴 | **Watchers:** {repo_info['watchers']} 👀\n"
                report += f"**Issues:** {repo_info['issues']} | **Size:** {repo_info['size']} KB\n"
                report += f"**License:** {repo_info['license']}\n"
                report += f"**Created:** {repo_info['created'][:10]}\n"
                report += f"**Last Updated:** {repo_info['updated'][:10]}\n"
                if repo_info['topics']:
                    report += f"**Topics:** {', '.join(repo_info['topics'])}\n"
                report += f"**URL:** {repo_info['url']}\n"
                
                if repo_info['readme']:
                    report += f"\n**README Preview:**\n{repo_info['readme'][:500]}..."
                
                return report
                
        except Exception as e:
            return f"❌ Failed to scrape GitHub repo {repo}: {e}"
    
    def scrape_api(self, api_url):
        """Scrape JSON API endpoint"""
        if not api_url.strip():
            return "❌ Please provide an API URL"
        
        if not api_url.startswith(('http://', 'https://')):
            api_url = 'https://' + api_url
        
        try:
            req = urllib.request.Request(api_url, headers=self.headers)
            
            with urllib.request.urlopen(req, timeout=self.config.get("timeout", 10)) as response:
                content = response.read().decode('utf-8')
                
                # Try to parse as JSON
                try:
                    api_data = json.loads(content)
                    data_type = 'json_api'
                except json.JSONDecodeError:
                    # If not JSON, treat as text
                    api_data = content
                    data_type = 'text_api'
                
                self.scraped_apis[api_url] = {
                    'timestamp': datetime.now().isoformat(),
                    'type': data_type,
                    'data': api_data,
                    'content_length': len(content)
                }
                
                # Add to history
                self.scraping_history.append({
                    'url': api_url,
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'type': 'api'
                })
                
                if data_type == 'json_api':
                    return f"✅ **API Data Retrieved:** {api_url}\n\n**📊 Summary:**\n• Data type: JSON\n• Content length: {len(content)} chars\n• Keys: {list(api_data.keys()) if isinstance(api_data, dict) else 'N/A'}\n• Items: {len(api_data) if isinstance(api_data, (list, dict)) else 'N/A'}"
                else:
                    return f"✅ **API Data Retrieved:** {api_url}\n\n**📊 Summary:**\n• Data type: Text\n• Content length: {len(content)} chars"
                
        except Exception as e:
            return f"❌ Failed to scrape API {api_url}: {e}"
    
    def search_web(self, engine, query):
        """Search the web using different search engines"""
        if not query.strip():
            return "❌ Please provide a search query"
        
        search_urls = {
            'google': f"https://www.google.com/search?q={urllib.parse.quote(query)}",
            'bing': f"https://www.bing.com/search?q={urllib.parse.quote(query)}",
            'duckduckgo': f"https://duckduckgo.com/?q={urllib.parse.quote(query)}",
            'github': f"https://github.com/search?q={urllib.parse.quote(query)}",
            'stackoverflow': f"https://stackoverflow.com/search?q={urllib.parse.quote(query)}"
        }
        
        if engine not in search_urls:
            return f"❌ Unknown search engine: {engine}\nAvailable: {', '.join(search_urls.keys())}"
        
        search_url = search_urls[engine]
        result = self.scrape_url(search_url)
        
        if "✅" in result:
            return f"🔍 **Search Results for '{query}' on {engine.title()}**\n\n{result}"
        else:
            return result
    
    def scrape_news(self, topic):
        """Scrape news about a specific topic"""
        # Use a news aggregator or search
        news_url = f"https://news.google.com/search?q={urllib.parse.quote(topic)}"
        result = self.scrape_url(news_url)
        
        if "✅" in result:
            return f"📰 **News about '{topic}'**\n\n{result}"
        else:
            return result
    
    def analyze_scraped_data(self, key=""):
        """Analyze scraped data"""
        if key and key in self.scraped_data:
            data = self.scraped_data[key]
            
            analysis = f"🔍 **Analysis for: {key}**\n\n"
            analysis += f"**Timestamp:** {data.get('timestamp', 'Unknown')}\n"
            analysis += f"**Content Length:** {data.get('content_length', 0)} chars\n"
            
            if 'text_content' in data:
                text = data['text_content']
                words = len(text.split())
                lines = len(text.split('\n'))
                analysis += f"**Word Count:** {words}\n"
                analysis += f"**Line Count:** {lines}\n"
                
                # Simple keyword analysis
                common_words = {}
                for word in text.lower().split():
                    word = re.sub(r'[^\w]', '', word)
                    if len(word) > 3:
                        common_words[word] = common_words.get(word, 0) + 1
                
                top_words = sorted(common_words.items(), key=lambda x: x[1], reverse=True)[:10]
                if top_words:
                    analysis += f"**Top Keywords:** {', '.join([f'{word}({count})' for word, count in top_words])}\n"
            
            if 'links' in data:
                analysis += f"**Links Found:** {len(data['links'])}\n"
            
            if 'images' in data:
                analysis += f"**Images Found:** {len(data['images'])}\n"
            
            if 'emails' in data:
                analysis += f"**Emails Found:** {len(data['emails'])}\n"
            
            return analysis
        
        elif not key:
            # General analysis
            total_items = len(self.scraped_data)
            total_apis = len(self.scraped_apis)
            
            if total_items == 0 and total_apis == 0:
                return "📊 No scraped data to analyze"
            
            analysis = f"📊 **General Data Analysis**\n\n"
            analysis += f"**Total URLs scraped:** {total_items}\n"
            analysis += f"**Total APIs scraped:** {total_apis}\n"
            
            if self.scraping_history:
                successful = len([h for h in self.scraping_history if h.get('success', False)])
                failed = len(self.scraping_history) - successful
                analysis += f"**Success rate:** {successful}/{len(self.scraping_history)} ({(successful/len(self.scraping_history)*100):.1f}%)\n"
            
            # Most recent scrapes
            recent = self.scraping_history[-5:]
            if recent:
                analysis += f"\n**Recent Activity:**\n"
                for entry in recent:
                    status = "✅" if entry.get('success', False) else "❌"
                    analysis += f"• {status} {entry.get('url', 'Unknown')} ({entry.get('timestamp', '')[:16]})\n"
            
            return analysis
        
        else:
            return f"❌ No data found for key: {key}"
    
    def extract_data(self, data_type, key=""):
        """Extract specific types of data"""
        if not key:
            available_keys = list(self.scraped_data.keys()) + list(self.scraped_apis.keys())
            return f"Available data keys: {', '.join(available_keys[:10])}{'...' if len(available_keys) > 10 else ''}"
        
        data = self.scraped_data.get(key) or self.scraped_apis.get(key)
        if not data:
            return f"❌ No data found for key: {key}"
        
        if data_type == "links":
            links = data.get('links', [])
            if not links:
                return f"No links found in {key}"
            
            result = f"🔗 **Links from {key}:**\n\n"
            for i, link in enumerate(links[:20], 1):  # Limit to 20
                if isinstance(link, dict):
                    result += f"{i}. {link.get('text', 'No text')}\n   {link.get('url', '')}\n\n"
                else:
                    result += f"{i}. {link}\n\n"
            
            if len(links) > 20:
                result += f"(Showing 20 of {len(links)} links)"
            
            return result
        
        elif data_type == "images":
            images = data.get('images', [])
            if not images:
                return f"No images found in {key}"
            
            result = f"🖼️ **Images from {key}:**\n\n"
            for i, img in enumerate(images[:15], 1):  # Limit to 15
                result += f"{i}. {img}\n"
            
            if len(images) > 15:
                result += f"\n(Showing 15 of {len(images)} images)"
            
            return result
        
        elif data_type == "emails":
            emails = data.get('emails', [])
            if not emails:
                return f"No emails found in {key}"
            
            return f"📧 **Emails from {key}:**\n\n{', '.join(emails)}"
        
        elif data_type == "text":
            text = data.get('text_content', data.get('data', ''))
            if not text:
                return f"No text content found in {key}"
            
            # Return first 1000 characters
            if len(str(text)) > 1000:
                return f"📄 **Text from {key}:**\n\n{str(text)[:1000]}...\n\n(Showing first 1000 characters)"
            else:
                return f"📄 **Text from {key}:**\n\n{text}"
        
        elif data_type == "metadata":
            metadata = data.get('metadata', {})
            if not metadata:
                return f"No metadata found in {key}"
            
            result = f"📋 **Metadata from {key}:**\n\n"
            for meta_key, meta_value in metadata.items():
                result += f"• {meta_key}: {meta_value}\n"
            
            return result
        
        else:
            return f"❌ Unknown data type: {data_type}\nAvailable: links, images, emails, text, metadata"
    
    def list_scraped_data(self, filter_type="all"):
        """List scraped data with optional filtering"""
        all_data = {}
        all_data.update(self.scraped_data)
        all_data.update(self.scraped_apis)
        
        if not all_data:
            return "📂 No scraped data available"
        
        if filter_type == "recent":
            # Show only recent data (last 24 hours)
            recent_data = {}
            for key, data in all_data.items():
                timestamp = data.get('timestamp', '')
                try:
                    data_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    now = datetime.now()
                    if (now - data_time).total_seconds() < 86400:  # 24 hours
                        recent_data[key] = data
                except:
                    pass
            all_data = recent_data
        
        elif filter_type == "urls":
            all_data = self.scraped_data
        
        elif filter_type == "apis":
            all_data = self.scraped_apis
        
        result = f"📂 **Scraped Data ({filter_type}):** {len(all_data)} items\n\n"
        
        for key, data in list(all_data.items())[:20]:  # Limit to 20 items
            timestamp = data.get('timestamp', 'Unknown')[:16]
            data_type = data.get('type', 'url')
            content_length = data.get('content_length', len(str(data.get('data', ''))))
            
            result += f"• **{key[:60]}{'...' if len(key) > 60 else ''}**\n"
            result += f"  Type: {data_type} | Size: {content_length} chars | Time: {timestamp}\n\n"
        
        if len(all_data) > 20:
            result += f"(Showing 20 of {len(all_data)} items)"
        
        return result
    
    def show_history(self, count=10):
        """Show scraping history"""
        if not self.scraping_history:
            return "📝 No scraping history available"
        
        recent_history = self.scraping_history[-count:]
        result = f"📝 **Scraping History (Last {len(recent_history)} entries):**\n\n"
        
        for i, entry in enumerate(recent_history, 1):
            timestamp = entry.get('timestamp', 'Unknown')[:16]
            url = entry.get('url', 'Unknown')
            success = "✅" if entry.get('success', False) else "❌"
            data_size = entry.get('data_size', 0)
            
            result += f"{i:2d}. {success} {url[:50]}{'...' if len(url) > 50 else ''}\n"
            result += f"    {timestamp}"
            if data_size:
                result += f" | {data_size} chars"
            if not entry.get('success', False) and entry.get('error'):
                result += f" | {entry['error'][:30]}..."
            result += "\n\n"
        
        return result
    
    def clear_data(self, data_type="data"):
        """Clear scraped data"""
        if data_type == "data":
            count = len(self.scraped_data)
            self.scraped_data.clear()
            return f"🗑️ Cleared {count} scraped URL entries"
        
        elif data_type == "apis":
            count = len(self.scraped_apis)
            self.scraped_apis.clear()
            return f"🗑️ Cleared {count} API entries"
        
        elif data_type == "history":
            count = len(self.scraping_history)
            self.scraping_history.clear()
            self.save_history()
            return f"🗑️ Cleared {count} history entries"
        
        elif data_type == "all":
            url_count = len(self.scraped_data)
            api_count = len(self.scraped_apis)
            history_count = len(self.scraping_history)
            
            self.scraped_data.clear()
            self.scraped_apis.clear()
            self.scraping_history.clear()
            self.save_history()
            
            return f"🗑️ Cleared all data: {url_count} URLs, {api_count} APIs, {history_count} history entries"
        
        else:
            return f"❌ Unknown data type: {data_type}\nAvailable: data, apis, history, all"
    
    def handle_config(self, config_command):
        """Handle configuration commands"""
        if "=" in config_command:
            key, value_str = config_command.split("=", 1)
            key = key.strip()
            value_str = value_str.strip()
            
            # Type conversion based on key
            try:
                if key in ["timeout", "max_retries", "max_content_length"]:
                    value = int(value_str)
                elif key == "delay_between_requests":
                    value = float(value_str)
                elif key in ["auto_save_data", "extract_links", "extract_images", "extract_emails", "respect_robots_txt"]:
                    value = value_str.lower() in ["true", "1", "yes"]
                else:
                    value = value_str
                
                self.config[key] = value
                self.save_config()
                return f"⚙️ Set {key} = {value}"
                
            except ValueError:
                return f"❌ Invalid value for {key}: {value_str}"
        else:
            key = config_command.strip()
            if key in self.config:
                return f"⚙️ {key} = {self.config[key]}"
            else:
                return f"❌ Config key '{key}' not found"
    
    def show_config(self):
        """Show all configuration settings"""
        result = "⚙️ **Web Scraper Configuration:**\n\n"
        for key, value in self.config.items():
            result += f"• {key} = {value}\n"
        
        result += "\n**To change:** scrape:config:key=value"
        return result
    
    def show_statistics(self):
        """Show comprehensive statistics"""
        total_urls = len(self.scraped_data)
        total_apis = len(self.scraped_apis)
        total_history = len(self.scraping_history)
        
        if total_history == 0:
            return "📊 No scraping activity yet"
        
        # Calculate success rate
        successful = len([h for h in self.scraping_history if h.get('success', False)])
        success_rate = (successful / total_history) * 100 if total_history > 0 else 0
        
        # Calculate total data scraped
        total_chars = sum(data.get('content_length', 0) for data in self.scraped_data.values())
        total_chars += sum(data.get('content_length', 0) for data in self.scraped_apis.values())
        
        # Most active days
        dates = {}
        for entry in self.scraping_history:
            date = entry.get('timestamp', '')[:10]
            dates[date] = dates.get(date, 0) + 1
        
        most_active = sorted(dates.items(), key=lambda x: x[1], reverse=True)[:5]
        
        result = f"""📊 **Web Scraper Statistics:**

**📈 Activity:**
• Total scraping attempts: {total_history}
• Successful scrapes: {successful}
• Success rate: {success_rate:.1f}%
• URLs scraped: {total_urls}
• APIs scraped: {total_apis}

**📊 Data:**
• Total characters scraped: {total_chars:,}
• Average per scrape: {total_chars // max(successful, 1):,} chars

**⚙️ Settings:**
• Timeout: {self.config.get('timeout', 10)}s
• Max retries: {self.config.get('max_retries', 3)}
• Delay between requests: {self.config.get('delay_between_requests', 1.0)}s
• Auto-save: {self.config.get('auto_save_data', True)}

**📅 Most Active Days:**"""
        
        for date, count in most_active:
            result += f"\n• {date}: {count} scrapes"
        
        # Recent activity
        recent = self.scraping_history[-5:]
        if recent:
            result += f"\n\n**🕒 Recent Activity:**"
            for entry in recent:
                status = "✅" if entry.get('success', False) else "❌"
                url = entry.get('url', 'Unknown')[:30]
                timestamp = entry.get('timestamp', '')[:16]
                result += f"\n• {status} {url}... ({timestamp})"
        
        return result
    
    def export_to_pxbot(self, name):
        """Export scraped data to PXBot code"""
        if not self.pxbot:
            return "❌ No PXBot instance available"
        
        if not self.scraped_data and not self.scraped_apis:
            return "❌ No scraped data to export"
        
        try:
            # Prepare export data
            export_data = {
                'scraped_urls': self.scraped_data,
                'scraped_apis': self.scraped_apis,
                'scraping_history': self.scraping_history[-50:],  # Last 50 entries
                'config': self.config,
                'export_timestamp': datetime.now().isoformat(),
                'statistics': {
                    'total_urls': len(self.scraped_data),
                    'total_apis': len(self.scraped_apis),
                    'total_attempts': len(self.scraping_history),
                    'successful_scrapes': len([h for h in self.scraping_history if h.get('success', False)])
                }
            }
            
            code = f'''# Web Scraper Export: {name}
# Generated on {datetime.now().isoformat()}

import json
from datetime import datetime

class WebScraperData:
    """Exported web scraping data and analysis tools"""
    
    def __init__(self):
        self.data = {json.dumps(export_data, indent=2, default=str)}
    
    def get_scraped_urls(self):
        """Get all scraped URL data"""
        return self.data.get('scraped_urls', {{}})
    
    def get_scraped_apis(self):
        """Get all scraped API data"""  
        return self.data.get('scraped_apis', {{}})
    
    def get_history(self):
        """Get scraping history"""
        return self.data.get('scraping_history', [])
    
    def get_statistics(self):
        """Get scraping statistics"""
        stats = self.data.get('statistics', {{}})
        return f"""📊 Scraping Statistics:
• URLs scraped: {{stats.get('total_urls', 0)}}
• APIs scraped: {{stats.get('total_apis', 0)}}
• Total attempts: {{stats.get('total_attempts', 0)}}
• Successful: {{stats.get('successful_scrapes', 0)}}
• Success rate: {{(stats.get('successful_scrapes', 0) / max(stats.get('total_attempts', 1), 1) * 100):.1f}}%"""
    
    def search_content(self, query):
        """Search scraped content for specific terms"""
        query = query.lower()
        results = []
        
        # Search URL data
        for url, data in self.get_scraped_urls().items():
            text_content = data.get('text_content', '').lower()
            title = data.get('title', '').lower()
            
            if query in text_content or query in title:
                results.append({{
                    'type': 'url',
                    'source': url,
                    'title': data.get('title', 'No title'),
                    'timestamp': data.get('timestamp', 'Unknown'),
                    'relevance': text_content.count(query) + title.count(query) * 2
                }})
        
        # Search API data
        for api_url, data in self.get_scraped_apis().items():
            api_content = str(data.get('data', '')).lower()
            
            if query in api_content:
                results.append({{
                    'type': 'api',
                    'source': api_url,
                    'timestamp': data.get('timestamp', 'Unknown'),
                    'relevance': api_content.count(query)
                }})
        
        # Sort by relevance
        results.sort(key=lambda x: x['relevance'], reverse=True)
        
        return results[:10]  # Top 10 results
    
    def get_links_by_domain(self):
        """Analyze links by domain"""
        domain_links = {{}}
        
        for url, data in self.get_scraped_urls().items():
            links = data.get('links', [])
            for link in links:
                link_url = link.get('url', '') if isinstance(link, dict) else str(link)
                try:
                    from urllib.parse import urlparse
                    domain = urlparse(link_url).netloc
                    if domain:
                        if domain not in domain_links:
                            domain_links[domain] = []
                        domain_links[domain].append(link_url)
                except:
                    pass
        
        return domain_links
    
    def export_summary(self):
        """Export a comprehensive summary"""
        print("🕷️ Web Scraper Data Summary")
        print("=" * 50)
        print(self.get_statistics())
        
        urls = self.get_scraped_urls()
        apis = self.get_scraped_apis()
        
        if urls:
            print("\\n📄 Scraped URLs:")
            for i, (url, data) in enumerate(list(urls.items())[:10], 1):
                title = data.get('title', 'No title')[:50]
                timestamp = data.get('timestamp', 'Unknown')[:16]
                print(f"  {{i:2d}}. {{title}} ({{timestamp}})")
                print(f"      {{url[:70]}}...")
        
        if apis:
            print("\\n🔌 Scraped APIs:")
            for i, (api_url, data) in enumerate(list(apis.items())[:5], 1):
                timestamp = data.get('timestamp', 'Unknown')[:16]
                print(f"  {{i}}. {{api_url[:70]}}... ({{timestamp}})")

# Create data instance
scraper_data = WebScraperData()

# Auto-display when imported
if __name__ == "__main__":
    scraper_data.export_summary()
'''
            
            result = self.pxbot.run(f"save:{name}:{code}")
            return f"📤 Exported scraping data to PXBot as '{name}': {result}"
            
        except Exception as e:
            return f"❌ Export error: {e}"
    
    def show_help(self):
        """Show comprehensive help"""
        return """🕷️ **Advanced Web Scraper Help:**

**🌐 Basic Scraping:**
• `scrape:url:example.com` - Scrape single URL
• `scrape:bulk:url1,url2,url3` - Scrape multiple URLs
• `scrape:github:user/repo` - Scrape GitHub repository
• `scrape:api:api.example.com/data` - Scrape JSON API

**🔍 Search & News:**
• `scrape:search:google:python tutorial` - Search Google
• `scrape:search:github:machine learning` - Search GitHub
• `scrape:news:artificial intelligence` - Get news

**📊 Data Management:**
• `scrape:list` - List all scraped data
• `scrape:list:recent` - List recent scrapes
• `scrape:list:apis` - List API scrapes only
• `scrape:analyze:url` - Analyze specific data
• `scrape:analyze` - General analysis

**🔧 Data Extraction:**
• `scrape:extract:links:url` - Extract links
• `scrape:extract:images:url` - Extract images
• `scrape:extract:emails:url` - Extract emails
• `scrape:extract:text:url` - Extract text content

**📝 History & Cleanup:**
• `scrape:history` - Show scraping history
• `scrape:history:20` - Show last 20 entries
• `scrape:clear:data` - Clear scraped data
• `scrape:clear:history` - Clear history
• `scrape:clear:all` - Clear everything

**⚙️ Configuration:**
• `scrape:config` - Show all settings
• `scrape:config:timeout=15` - Set timeout
• `scrape:config:extract_links=true` - Enable link extraction
• `scrape:config:delay_between_requests=2.0` - Set delay

**📊 Analysis & Export:**
• `scrape:stats` - Show comprehensive statistics
• `scrape:export:project_data` - Export to PXBot

**💡 Examples:**
```
scrape:url:python.org
scrape:github:python/cpython
scrape:api:api.github.com/repos/python/cpython
scrape:search:stackoverflow:python web scraping
scrape:extract:links:python.org
scrape:analyze:python.org
scrape:export:python_research
```

**⚙️ Available Settings:**
• timeout (seconds): Request timeout
• max_retries: Number of retry attempts
• delay_between_requests (seconds): Delay between requests
• max_content_length (bytes): Maximum content size
• extract_links/images/emails (true/false): What to extract
• auto_save_data (true/false): Auto-save to disk
"""
    
    def cleanup(self):
        """Cleanup when app is unloaded"""
        self.save_config()
        self.save_history()

# Required main function
def main():
    """Entry point for the web scraper app"""
    return AdvancedWebScraper()

# For direct testing
if __name__ == "__main__":
    app = main()
    print("🕷️ Advanced Web Scraper Test")
    print("=" * 40)
    
    # Test basic functionality
    print(app.execute_command("scrape:config"))
    print("\n" + app.execute_command("scrape:url:httpbin.org/json"))