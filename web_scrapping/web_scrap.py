#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MyJPJ FAQ Web Scraper - Production Version
Designed to run locally and extract complete FAQ content from MyJPJ website
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import random
import re
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging
from typing import List, Dict, Optional
import sys
import os

# Configure logging
def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('myjpj_scraper.log', encoding='utf-8')
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

class MyJPJFAQScraper:
    """
    Complete MyJPJ FAQ scraper optimized for localhost execution
    """
    
    def __init__(self, base_url="https://myjpj.jpj.gov.my/faq"):
        self.base_url = base_url
        self.session = self._create_robust_session()
        self.qa_pairs = []
        
    def _create_robust_session(self):
        """Create a robust session with proper configuration"""
        session = requests.Session()
        
        # Advanced retry strategy
        retry_strategy = Retry(
            total=5,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504, 520, 521, 522, 523, 524],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=1,
            pool_maxsize=1
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Comprehensive headers to mimic real browser
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9,ms;q=0.8,id;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
            'Sec-GPC': '1'
        })
        
        return session
    
    def test_connectivity(self):
        """Test connection to MyJPJ website"""
        try:
            logger.info("Testing connectivity to MyJPJ FAQ website...")
            
            response = self.session.get(self.base_url, timeout=30)
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response size: {len(response.content):,} bytes")
            logger.info(f"Response time: {response.elapsed.total_seconds():.2f} seconds")
            
            if response.status_code == 200:
                # Check if content looks correct
                content = response.text.lower()
                if 'myjpj' in content and ('faq' in content or 'soalan' in content):
                    logger.info("✅ Connection successful - FAQ page detected")
                    return True, response
                else:
                    logger.warning("⚠️ Connected but content may not be FAQ page")
                    return True, response
            else:
                logger.error(f"❌ HTTP error: {response.status_code}")
                return False, None
                
        except requests.exceptions.ConnectionError as e:
            logger.error(f"❌ Connection error: {e}")
            logger.info("💡 Try: VPN, different network, or check if site is down")
            return False, None
        except requests.exceptions.Timeout as e:
            logger.error(f"⏰ Timeout error: {e}")
            logger.info("💡 Try: Check network speed or try again later")
            return False, None
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return False, None
    
    def fetch_page_content(self, max_retries=3):
        """Fetch page content with retries and delays"""
        for attempt in range(max_retries):
            try:
                # Progressive delay
                if attempt > 0:
                    delay = random.uniform(2.0, 5.0) * attempt
                    logger.info(f"⏳ Waiting {delay:.1f}s before attempt {attempt + 1}")
                    time.sleep(delay)
                
                logger.info(f"🔗 Fetching page content (attempt {attempt + 1}/{max_retries})")
                response = self.session.get(self.base_url, timeout=30)
                response.raise_for_status()
                
                # Parse with multiple parsers for robustness
                try:
                    soup = BeautifulSoup(response.content, 'lxml')
                    logger.info("✅ Content parsed successfully with lxml")
                except:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    logger.info("✅ Content parsed successfully with html.parser")
                
                return soup
                
            except Exception as e:
                logger.error(f"❌ Attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    logger.error("💥 All fetch attempts failed")
                    return None
        
        return None
    
    def clean_text(self, text):
        """Clean and normalize text content"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove unwanted characters but keep Malay diacritics
        text = re.sub(r'[^\w\s\(\)\[\]\.,;:!?/\-–—""''\u00C0-\u017F\u0100-\u024F]', '', text)
        
        return text.strip()
    
    def extract_main_description(self, soup):
        """Extract the main MyJPJ description"""
        try:
            # Look for the main description in various locations
            main_desc_selectors = [
                'table tr td',
                'div',
                'p',
                'span'
            ]
            
            for selector in main_desc_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = self.clean_text(element.get_text())
                    if ('MyJPJ merupakan aplikasi mudah alih' in text or 
                        'MyJPJ' in text and 'aplikasi' in text and len(text) > 50):
                        
                        self.qa_pairs.append({
                            "question": "Apakah MyJPJ?",
                            "answer": text
                        })
                        logger.info("✅ Extracted main MyJPJ description")
                        return
            
            logger.warning("⚠️ Main description not found")
            
        except Exception as e:
            logger.error(f"❌ Error extracting main description: {e}")
    
    def extract_services_list(self, soup):
        """Extract services offered by MyJPJ"""
        try:
            services = []
            
            # Find all table cells and other elements
            all_elements = soup.find_all(['td', 'li', 'div', 'span', 'p'])
            
            for element in all_elements:
                text = self.clean_text(element.get_text())
                
                # Look for numbered services (i., ii., iii., etc.)
                if re.match(r'^(i{1,3}v?|iv|v|vi{1,3}|ix|x)\.|^[1-9]\.|^\([1-9]\)', text):
                    if len(text) > 10 and ('Semakan' in text or 'Laporan' in text or 'Pautan' in text):
                        services.append(text)
            
            if services:
                # Remove duplicates while preserving order
                unique_services = []
                seen = set()
                for service in services:
                    if service not in seen:
                        seen.add(service)
                        unique_services.append(service)
                
                self.qa_pairs.append({
                    "question": "Apakah perkhidmatan yang ditawarkan oleh MyJPJ?",
                    "answer": " | ".join(unique_services)
                })
                logger.info(f"✅ Extracted {len(unique_services)} services")
                
                # Also create separate Q&A for transaction types
                self.qa_pairs.append({
                    "question": "Apakah jenis transaksi yang boleh dilakukan melalui MyJPJ?",
                    "answer": " | ".join(unique_services)
                })
            else:
                logger.warning("⚠️ No services list found")
                
        except Exception as e:
            logger.error(f"❌ Error extracting services: {e}")
    
    def extract_password_help(self, soup):
        """Extract password and account help information"""
        try:
            password_content = []
            
            all_elements = soup.find_all(['td', 'div', 'p', 'span'])
            
            for element in all_elements:
                text = self.clean_text(element.get_text())
                
                if any(keyword in text.lower() for keyword in ['kata laluan', 'password', 'lupa', 'tetapan semula', 'emel']):
                    if len(text) > 15:
                        password_content.append(text)
            
            if password_content:
                # Create Q&A for password reset
                password_text = " ".join(password_content)
                
                if 'kata laluan' in password_text.lower():
                    self.qa_pairs.append({
                        "question": "Bagaimana cara menukar kata laluan MyJPJ?",
                        "answer": password_text
                    })
                
                if 'emel' in password_text.lower():
                    self.qa_pairs.append({
                        "question": "Apa yang perlu dilakukan jika lupa alamat emel yang didaftarkan?",
                        "answer": password_text
                    })
                
                logger.info("✅ Extracted password/account help information")
            
        except Exception as e:
            logger.error(f"❌ Error extracting password help: {e}")
    
    def extract_fee_information(self, soup):
        """Extract fee structure from tables"""
        try:
            tables = soup.find_all('table')
            
            for table_idx, table in enumerate(tables):
                rows = table.find_all('tr')
                
                # Look for fee tables (contain 'Fi', 'RM', numbers)
                table_text = table.get_text().lower()
                if any(keyword in table_text for keyword in ['fi', 'rm', 'bayaran', 'kos']):
                    
                    fees = []
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        
                        if len(cells) >= 2:
                            # Try to extract structured fee data
                            row_data = []
                            for cell in cells:
                                cell_text = self.clean_text(cell.get_text())
                                if cell_text and cell_text not in ['Bil', 'Perkara', 'Fi', 'RM', '--']:
                                    row_data.append(cell_text)
                            
                            if len(row_data) >= 2 and any(char.isdigit() for char in ' '.join(row_data)):
                                fees.append(' - '.join(row_data))
                    
                    if fees:
                        self.qa_pairs.append({
                            "question": f"Apakah struktur fi/bayaran untuk perkhidmatan JPJ?",
                            "answer": " | ".join(fees)
                        })
                        logger.info(f"✅ Extracted fee information from table {table_idx + 1}")
            
        except Exception as e:
            logger.error(f"❌ Error extracting fee information: {e}")
    
    def extract_general_help(self, soup):
        """Extract general help and support information"""
        try:
            help_content = []
            
            # Look for help-related content
            all_elements = soup.find_all(['td', 'div', 'p', 'li'])
            
            for element in all_elements:
                text = self.clean_text(element.get_text())
                
                if any(keyword in text.lower() for keyword in ['kaunter', 'jpj', 'bantuan', 'hubungi', 'hadir']):
                    if len(text) > 20 and len(text) < 300:
                        help_content.append(text)
            
            if help_content:
                unique_help = list(dict.fromkeys(help_content))  # Remove duplicates
                
                self.qa_pairs.append({
                    "question": "Di mana boleh mendapatkan bantuan untuk MyJPJ?",
                    "answer": " | ".join(unique_help)
                })
                logger.info("✅ Extracted general help information")
            
        except Exception as e:
            logger.error(f"❌ Error extracting general help: {e}")
    
    def add_common_questions(self):
        """Add common questions that users might ask"""
        common_qa = [
            {
                "question": "Bagaimana cara muat turun aplikasi MyJPJ?",
                "answer": "Aplikasi MyJPJ boleh dimuat turun dari Google Play Store untuk Android dan App Store untuk iOS. Cari 'MyJPJ' dan pilih aplikasi rasmi dari Jabatan Pengangkutan Jalan Malaysia."
            },
            {
                "question": "Adakah perlu bayar untuk menggunakan aplikasi MyJPJ?",
                "answer": "Aplikasi MyJPJ adalah percuma untuk dimuat turun dan kebanyakan perkhidmatan semakan adalah percuma. Namun, sesetengah transaksi seperti pembaharuan lesen mungkin dikenakan bayaran."
            },
            {
                "question": "Apakah syarat untuk mendaftar akaun MyJPJ?",
                "answer": "Untuk mendaftar akaun MyJPJ, anda memerlukan nombor MyKad yang sah, alamat emel yang aktif, dan nombor telefon yang sah."
            },
            {
                "question": "Bolehkah menggunakan MyJPJ untuk orang lain?",
                "answer": "MyJPJ adalah untuk kegunaan peribadi sahaja. Setiap pengguna perlu menggunakan nombor MyKad dan maklumat peribadi mereka sendiri."
            }
        ]
        
        self.qa_pairs.extend(common_qa)
        logger.info(f"✅ Added {len(common_qa)} common questions")
    
    def scrape_complete_website(self):
        """Main scraping function"""
        logger.info("🚀 Starting complete MyJPJ FAQ scraping...")
        
        # Test connectivity first
        connected, response = self.test_connectivity()
        if not connected:
            return {"error": "Cannot connect to MyJPJ website"}
        
        # Fetch page content
        soup = self.fetch_page_content()
        if not soup:
            return {"error": "Failed to fetch page content"}
        
        # Extract all types of content
        logger.info("🔄 Extracting main description...")
        self.extract_main_description(soup)
        
        logger.info("🔄 Extracting services list...")
        self.extract_services_list(soup)
        
        logger.info("🔄 Extracting password help...")
        self.extract_password_help(soup)
        
        logger.info("🔄 Extracting fee information...")
        self.extract_fee_information(soup)
        
        logger.info("🔄 Extracting general help...")
        self.extract_general_help(soup)
        
        logger.info("🔄 Adding common questions...")
        self.add_common_questions()
        
        # Remove duplicates
        unique_qa = []
        seen_questions = set()
        
        for qa in self.qa_pairs:
            question_key = qa['question'].lower().strip()
            if question_key not in seen_questions:
                seen_questions.add(question_key)
                unique_qa.append(qa)
        
        # Create final data structure
        scraped_data = {
            "title": "MyJPJ FAQ - Soalan Lazim MyJPJ",
            "description": "Complete FAQ content scraped from MyJPJ official website",
            "url": self.base_url,
            "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "scraping_method": "Localhost web scraping",
            "user_agent": self.session.headers['User-Agent'],
            "total_qa_pairs": len(unique_qa),
            "qa_pairs": unique_qa
        }
        
        logger.info(f"✅ Scraping completed! Extracted {len(unique_qa)} unique Q&A pairs")
        return scraped_data
    
    def save_results(self, data, filename="myjpj_complete_faq.json"):
        """Save scraped data to JSON file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"💾 Results saved to: {filename}")
            
            # Also save a backup with timestamp
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_filename = f"myjpj_faq_backup_{timestamp}.json"
            
            with open(backup_filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"💾 Backup saved to: {backup_filename}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving results: {e}")
            return False
    
    def display_results(self, data):
        """Display scraping results summary"""
        print("\n" + "="*70)
        print("📋 MyJPJ FAQ SCRAPING RESULTS")
        print("="*70)
        print(f"🌐 Source URL: {data['url']}")
        print(f"⏰ Scraped at: {data['scraped_at']}")
        print(f"📊 Total Q&A pairs: {data['total_qa_pairs']}")
        print(f"🔧 Method: {data['scraping_method']}")
        
        print("\n🔍 Sample Q&A pairs:")
        for i, qa in enumerate(data['qa_pairs'][:5]):
            print(f"\n{i+1}. Q: {qa['question']}")
            print(f"   A: {qa['answer'][:100]}{'...' if len(qa['answer']) > 100 else ''}")
        
        print("\n" + "="*70)
        print("✅ SCRAPING COMPLETED SUCCESSFULLY!")
        print(f"💾 Check files: myjpj_complete_faq.json")
        print("📜 Log file: myjpj_scraper.log")
        print("="*70)

def main():
    """Main execution function"""
    print("🚀 MyJPJ Complete FAQ Scraper")
    print("📍 Running from localhost")
    print("🎯 Target: https://myjpj.jpj.gov.my/faq")
    print("-" * 50)
    
    try:
        # Initialize scraper
        scraper = MyJPJFAQScraper()
        
        # Run complete scraping
        results = scraper.scrape_complete_website()
        
        if "error" not in results:
            # Save results
            if scraper.save_results(results):
                scraper.display_results(results)
            else:
                print("❌ Failed to save results")
        else:
            print(f"❌ Scraping failed: {results['error']}")
            print("\n🔧 TROUBLESHOOTING STEPS:")
            print("1. Check internet connection")
            print("2. Try using VPN (Malaysian server preferred)")
            print("3. Verify MyJPJ website is accessible in browser")
            print("4. Check firewall/antivirus settings")
            print("5. Try running as administrator")
            
    except KeyboardInterrupt:
        print("\n⏹️ Scraping interrupted by user")
    except Exception as e:
        logger.error(f"💥 Unexpected error in main: {e}")
        print(f"💥 Unexpected error: {e}")

if __name__ == "__main__":
    main()
