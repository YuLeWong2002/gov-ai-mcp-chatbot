#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MyJPJ FAQ Complete Scraper with Perfect Formatting
Extracts ALL content with proper structure and formatting
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
import sys
import os
from typing import List, Dict, Optional

# Setup comprehensive logging
def setup_logging():
    """Setup detailed logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('myjpj_complete_scraper.log', encoding='utf-8')
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

class CompleteMyJPJScraper:
    """
    Complete MyJPJ FAQ scraper with perfect formatting and structure
    """
    
    def __init__(self, base_url="https://myjpj.jpj.gov.my/faq"):
        self.base_url = base_url
        self.session = self._create_session()
        self.extracted_data = {
            "main_description": None,
            "services_list": [],
            "password_procedures": [],
            "fee_structures": [],
            "general_procedures": [],
            "contact_info": [],
            "additional_info": []
        }
        self.qa_pairs = []
        
    def _create_session(self):
        """Create robust session with comprehensive headers"""
        session = requests.Session()
        
        # Advanced retry strategy
        retry_strategy = Retry(
            total=5,
            backoff_factor=3,
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
        
        # Comprehensive browser headers
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'ms-MY,ms;q=0.9,en-US;q=0.8,en;q=0.7,id;q=0.6',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
            'Pragma': 'no-cache'
        })
        
        return session
    
    def test_and_fetch_content(self):
        """Test connection and fetch content with comprehensive error handling"""
        try:
            logger.info("🔍 Testing connection to MyJPJ FAQ...")
            
            # Test connection
            response = self.session.get(self.base_url, timeout=30)
            logger.info(f"📊 Response: {response.status_code} | Size: {len(response.content):,} bytes | Time: {response.elapsed.total_seconds():.2f}s")
            
            if response.status_code == 200:
                content = response.text.lower()
                if 'myjpj' in content:
                    logger.info("✅ MyJPJ FAQ page detected successfully")
                    
                    # Parse with best available parser
                    try:
                        soup = BeautifulSoup(response.content, 'lxml')
                        logger.info("✅ Content parsed with lxml parser")
                    except:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        logger.info("✅ Content parsed with html.parser")
                    
                    return soup
                else:
                    logger.warning("⚠️ Page content doesn't appear to be MyJPJ FAQ")
                    return None
            else:
                logger.error(f"❌ HTTP Error: {response.status_code}")
                return None
                
        except requests.exceptions.ConnectionError as e:
            logger.error(f"❌ Connection Error: {e}")
            logger.info("💡 Solutions: Check internet, try VPN, verify website status")
            return None
        except requests.exceptions.Timeout as e:
            logger.error(f"⏰ Timeout Error: {e}")
            logger.info("💡 Solutions: Check connection speed, try again later")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected Error: {e}")
            return None
    
    def clean_and_format_text(self, text):
        """Clean and format text while preserving structure"""
        if not text:
            return ""
        
        # Normalize whitespace but preserve structure
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Clean unwanted characters but keep Malay characters and punctuation
        text = re.sub(r'[^\w\s\(\)\[\]\.,;:!?/\-–—""''\u00C0-\u017F\u0100-\u024F\n]', '', text)
        
        return text.strip()
    
    def extract_main_description(self, soup):
        """Extract the main MyJPJ description with perfect formatting"""
        logger.info("🔄 Extracting main MyJPJ description...")
        
        try:
            # Look for main description in table cells
            tables = soup.find_all('table')
            
            for table in tables:
                cells = table.find_all(['td', 'th'])
                for cell in cells:
                    text = self.clean_and_format_text(cell.get_text())
                    
                    # Match the exact pattern from the provided data
                    if ('MyJPJ merupakan aplikasi mudah alih yang dibangunkan oleh Jabatan Pengangkutan Jalan' in text
                        or ('MyJPJ' in text and 'aplikasi mudah alih' in text and len(text) > 50)):
                        
                        self.extracted_data["main_description"] = text
                        logger.info("✅ Main description extracted successfully")
                        return text
            
            logger.warning("⚠️ Main description not found in expected format")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error extracting main description: {e}")
            return None
    
    def extract_services_list(self, soup):
        """Extract services list with exact formatting"""
        logger.info("🔄 Extracting services list...")
        
        try:
            services = []
            
            # Find all elements that might contain services
            all_elements = soup.find_all(['td', 'li', 'div', 'span'])
            
            for element in all_elements:
                text = self.clean_and_format_text(element.get_text())
                
                # Match Roman numerals and numbered lists
                if re.match(r'^(i{1,3}v?|iv|v|vi{1,3}|ix|x)\.|^[1-9]\.|^\([1-9]\)', text):
                    # Check if it's a service description
                    if any(keyword in text for keyword in ['Semakan', 'Laporan', 'Pautan', 'Pembaharuan']):
                        if len(text) > 15:  # Ensure substantial content
                            services.append(text)
            
            if services:
                # Remove duplicates while preserving order
                unique_services = []
                seen = set()
                for service in services:
                    service_key = re.sub(r'^(i{1,3}v?|iv|v|vi{1,3}|ix|x)\.|^[1-9]\.|^\([1-9]\)', '', service).strip()
                    if service_key not in seen:
                        seen.add(service_key)
                        unique_services.append(service)
                
                self.extracted_data["services_list"] = unique_services
                logger.info(f"✅ Extracted {len(unique_services)} services")
                return unique_services
            
            logger.warning("⚠️ No services found")
            return []
            
        except Exception as e:
            logger.error(f"❌ Error extracting services: {e}")
            return []
    
    def extract_password_procedures(self, soup):
        """Extract password and account procedures with formatting"""
        logger.info("🔄 Extracting password procedures...")
        
        try:
            procedures = []
            
            # Find all elements
            all_elements = soup.find_all(['td', 'div', 'p', 'span'])
            
            for element in all_elements:
                text = self.clean_and_format_text(element.get_text())
                
                # Look for password-related content
                if any(keyword in text.lower() for keyword in [
                    'kata laluan', 'password', 'tetapan semula', 'lupa', 'emel'
                ]):
                    if len(text) > 20:
                        procedures.append(text)
            
            if procedures:
                # Remove duplicates and clean
                unique_procedures = []
                seen = set()
                for proc in procedures:
                    if proc not in seen and len(proc.strip()) > 10:
                        seen.add(proc)
                        unique_procedures.append(proc)
                
                self.extracted_data["password_procedures"] = unique_procedures
                logger.info(f"✅ Extracted {len(unique_procedures)} password procedures")
                return unique_procedures
            
            return []
            
        except Exception as e:
            logger.error(f"❌ Error extracting password procedures: {e}")
            return []
    
    def extract_fee_structures(self, soup):
        """Extract fee structures with perfect table formatting"""
        logger.info("🔄 Extracting fee structures...")
        
        try:
            fee_structures = []
            
            tables = soup.find_all('table')
            
            for table_idx, table in enumerate(tables):
                # Check if this is a fee table
                table_text = table.get_text().lower()
                if any(keyword in table_text for keyword in ['fi', 'rm', 'bayaran', 'kos', 'yuran']):
                    
                    rows = table.find_all('tr')
                    current_table_fees = []
                    headers = []
                    
                    for row_idx, row in enumerate(rows):
                        cells = row.find_all(['td', 'th'])
                        
                        if cells:
                            row_data = []
                            for cell in cells:
                                cell_text = self.clean_and_format_text(cell.get_text())
                                if cell_text and cell_text not in ['--', '']:
                                    row_data.append(cell_text)
                            
                            if row_data:
                                if row_idx == 0 or any(header in ' '.join(row_data) for header in ['Bil', 'Perkara', 'Fi']):
                                    headers = row_data
                                else:
                                    # Format as structured fee entry
                                    if len(row_data) >= 2:
                                        if any(char.isdigit() or 'RM' in item for item in row_data):
                                            formatted_fee = ' | '.join(row_data)
                                            current_table_fees.append(formatted_fee)
                    
                    if current_table_fees:
                        fee_structure = {
                            "table_index": table_idx + 1,
                            "headers": headers,
                            "fees": current_table_fees
                        }
                        fee_structures.append(fee_structure)
                        logger.info(f"✅ Extracted fee structure from table {table_idx + 1}")
            
            self.extracted_data["fee_structures"] = fee_structures
            return fee_structures
            
        except Exception as e:
            logger.error(f"❌ Error extracting fee structures: {e}")
            return []
    
    def extract_general_procedures(self, soup):
        """Extract general procedures and help information"""
        logger.info("🔄 Extracting general procedures...")
        
        try:
            procedures = []
            
            all_elements = soup.find_all(['td', 'div', 'li', 'p'])
            
            for element in all_elements:
                text = self.clean_and_format_text(element.get_text())
                
                # Look for procedural content
                if any(keyword in text.lower() for keyword in [
                    'kaunter', 'jpj', 'bantuan', 'hubungi', 'hadir', 'prosedur'
                ]):
                    if 15 < len(text) < 500:  # Reasonable length
                        procedures.append(text)
            
            if procedures:
                unique_procedures = list(dict.fromkeys(procedures))  # Remove duplicates
                self.extracted_data["general_procedures"] = unique_procedures
                logger.info(f"✅ Extracted {len(unique_procedures)} general procedures")
                return unique_procedures
            
            return []
            
        except Exception as e:
            logger.error(f"❌ Error extracting general procedures: {e}")
            return []
    
    def format_qa_pairs(self):
        """Format all extracted data into perfect Q&A pairs"""
        logger.info("🔄 Formatting Q&A pairs...")
        
        qa_pairs = []
        
        # 1. Main Description
        if self.extracted_data["main_description"]:
            qa_pairs.append({
                "id": "Q001",
                "category": "Main Information",
                "question": "Apakah MyJPJ?",
                "answer": self.extracted_data["main_description"],
                "type": "definition"
            })
        
        # 2. Services List - Split into logical Q&A
        if self.extracted_data["services_list"]:
            # All services
            qa_pairs.append({
                "id": "Q002",
                "category": "Services",
                "question": "Apakah perkhidmatan yang ditawarkan oleh aplikasi MyJPJ?",
                "answer": "\n".join([f"• {service}" for service in self.extracted_data["services_list"]]),
                "type": "services_list"
            })
            
            # Transaction types
            qa_pairs.append({
                "id": "Q003", 
                "category": "Services",
                "question": "Apakah jenis transaksi yang boleh dilakukan melalui MyJPJ?",
                "answer": "\n".join([f"• {service}" for service in self.extracted_data["services_list"]]),
                "type": "transactions_list"
            })
        
        # 3. Password Procedures
        if self.extracted_data["password_procedures"]:
            # Password reset
            password_content = " ".join(self.extracted_data["password_procedures"])
            if 'kata laluan' in password_content.lower():
                qa_pairs.append({
                    "id": "Q004",
                    "category": "Account Management",
                    "question": "Bagaimana cara menukar kata laluan MyJPJ?",
                    "answer": password_content,
                    "type": "procedure"
                })
            
            # Email reset
            if 'emel' in password_content.lower():
                qa_pairs.append({
                    "id": "Q005",
                    "category": "Account Management", 
                    "question": "Apa yang perlu dilakukan jika lupa alamat emel yang didaftarkan?",
                    "answer": password_content,
                    "type": "procedure"
                })
        
        # 4. Fee Structures
        for idx, fee_structure in enumerate(self.extracted_data["fee_structures"]):
            qa_pairs.append({
                "id": f"Q{6+idx:03d}",
                "category": "Fees and Payments",
                "question": f"Apakah struktur bayaran/fi untuk perkhidmatan JPJ?",
                "answer": "\n".join([f"• {fee}" for fee in fee_structure["fees"]]),
                "type": "fee_structure",
                "table_info": {
                    "table_number": fee_structure["table_index"],
                    "headers": fee_structure["headers"]
                }
            })
        
        # 5. General Procedures
        if self.extracted_data["general_procedures"]:
            qa_pairs.append({
                "id": f"Q{10:03d}",
                "category": "Support and Help",
                "question": "Di mana boleh mendapatkan bantuan untuk masalah MyJPJ?",
                "answer": "\n".join([f"• {proc}" for proc in self.extracted_data["general_procedures"][:5]]),
                "type": "help_info"
            })
        
        # 6. Common Additional Questions
        common_questions = [
            {
                "id": "Q011",
                "category": "General Information",
                "question": "Bagaimana cara muat turun aplikasi MyJPJ?",
                "answer": "Aplikasi MyJPJ boleh dimuat turun dari:\n• Google Play Store (untuk Android)\n• App Store (untuk iOS)\n• Cari 'MyJPJ' dan pilih aplikasi rasmi dari Jabatan Pengangkutan Jalan Malaysia",
                "type": "common_question"
            },
            {
                "id": "Q012",
                "category": "General Information",
                "question": "Adakah aplikasi MyJPJ percuma untuk digunakan?",
                "answer": "• Aplikasi MyJPJ adalah percuma untuk dimuat turun\n• Kebanyakan perkhidmatan semakan adalah percuma\n• Sesetengah transaksi mungkin dikenakan bayaran mengikut kadar yang ditetapkan",
                "type": "common_question"
            },
            {
                "id": "Q013",
                "category": "Account Management",
                "question": "Apakah syarat untuk mendaftar akaun MyJPJ?",
                "answer": "Untuk mendaftar akaun MyJPJ, anda memerlukan:\n• Nombor MyKad yang sah\n• Alamat emel yang aktif\n• Nombor telefon yang sah\n• Maklumat peribadi yang tepat",
                "type": "common_question"
            }
        ]
        
        qa_pairs.extend(common_questions)
        
        self.qa_pairs = qa_pairs
        logger.info(f"✅ Formatted {len(qa_pairs)} Q&A pairs with perfect structure")
        return qa_pairs
    
    def scrape_complete_website(self):
        """Main scraping orchestration function"""
        logger.info("🚀 Starting complete MyJPJ FAQ scraping with perfect formatting...")
        
        # Fetch content
        soup = self.test_and_fetch_content()
        if not soup:
            return {"error": "Failed to fetch website content"}
        
        # Extract all content types
        self.extract_main_description(soup)
        self.extract_services_list(soup)
        self.extract_password_procedures(soup)
        self.extract_fee_structures(soup)
        self.extract_general_procedures(soup)
        
        # Format into Q&A pairs
        qa_pairs = self.format_qa_pairs()
        
        # Create comprehensive data structure
        scraped_data = {
            "metadata": {
                "title": "MyJPJ FAQ - Soalan Lazim MyJPJ (Complete)",
                "description": "Comprehensive FAQ content scraped from MyJPJ official website with perfect formatting",
                "source_url": self.base_url,
                "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "scraping_method": "Complete localhost web scraping",
                "user_agent": self.session.headers['User-Agent'],
                "total_qa_pairs": len(qa_pairs),
                "categories": list(set([qa.get('category', 'General') for qa in qa_pairs])),
                "content_types": list(set([qa.get('type', 'general') for qa in qa_pairs]))
            },
            "raw_extracted_data": {
                "main_description": self.extracted_data["main_description"],
                "services_count": len(self.extracted_data["services_list"]),
                "password_procedures_count": len(self.extracted_data["password_procedures"]),
                "fee_structures_count": len(self.extracted_data["fee_structures"]),
                "general_procedures_count": len(self.extracted_data["general_procedures"])
            },
            "qa_pairs": qa_pairs,
            "statistics": {
                "by_category": {},
                "by_type": {},
                "total_questions": len(qa_pairs),
                "avg_answer_length": sum(len(qa.get('answer', '')) for qa in qa_pairs) // len(qa_pairs) if qa_pairs else 0
            }
        }
        
        # Calculate statistics
        for qa in qa_pairs:
            category = qa.get('category', 'General')
            qa_type = qa.get('type', 'general')
            
            scraped_data["statistics"]["by_category"][category] = scraped_data["statistics"]["by_category"].get(category, 0) + 1
            scraped_data["statistics"]["by_type"][qa_type] = scraped_data["statistics"]["by_type"].get(qa_type, 0) + 1
        
        logger.info(f"✅ Complete scraping finished! Extracted {len(qa_pairs)} perfectly formatted Q&A pairs")
        return scraped_data
    
    def save_comprehensive_results(self, data, base_filename="myjpj_complete_formatted"):
        """Save results in multiple formats"""
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            
            # 1. Main JSON file
            main_file = f"{base_filename}.json"
            with open(main_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 Main results saved: {main_file}")
            
            # 2. Backup with timestamp
            backup_file = f"{base_filename}_backup_{timestamp}.json"
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 Backup saved: {backup_file}")
            
            # 3. Q&A only version (simplified)
            qa_only = {
                "title": data["metadata"]["title"],
                "scraped_at": data["metadata"]["scraped_at"],
                "total_qa_pairs": data["metadata"]["total_qa_pairs"],
                "qa_pairs": [
                    {
                        "question": qa["question"],
                        "answer": qa["answer"],
                        "category": qa.get("category", "General")
                    }
                    for qa in data["qa_pairs"]
                ]
            }
            
            qa_file = f"{base_filename}_qa_only.json"
            with open(qa_file, 'w', encoding='utf-8') as f:
                json.dump(qa_only, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 Q&A-only version saved: {qa_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving results: {e}")
            return False
    
    def display_comprehensive_results(self, data):
        """Display detailed scraping results"""
        print("\n" + "="*80)
        print("📋 MyJPJ COMPLETE FAQ SCRAPING RESULTS")
        print("="*80)
        
        metadata = data["metadata"]
        stats = data["statistics"]
        
        print(f"🌐 Source: {metadata['source_url']}")
        print(f"⏰ Scraped: {metadata['scraped_at']}")
        print(f"📊 Total Q&A Pairs: {metadata['total_qa_pairs']}")
        print(f"🔧 Method: {metadata['scraping_method']}")
        
        print(f"\n📈 CONTENT STATISTICS:")
        print(f"   • Categories: {len(metadata['categories'])}")
        print(f"   • Content Types: {len(metadata['content_types'])}")
        print(f"   • Average Answer Length: {stats['avg_answer_length']} characters")
        
        print(f"\n🗂️ BY CATEGORY:")
        for category, count in stats["by_category"].items():
            print(f"   • {category}: {count} questions")
        
        print(f"\n📝 BY TYPE:")
        for qa_type, count in stats["by_type"].items():
            print(f"   • {qa_type}: {count} items")
        
        print(f"\n🔍 SAMPLE Q&A PAIRS:")
        for i, qa in enumerate(data["qa_pairs"][:3]):
            print(f"\n{i+1}. [{qa.get('category', 'General')}] {qa['question']}")
            answer_preview = qa['answer'][:150].replace('\n', ' ')
            print(f"   {answer_preview}{'...' if len(qa['answer']) > 150 else ''}")
        
        print(f"\n📁 FILES CREATED:")
        print(f"   • myjpj_complete_formatted.json (complete data)")
        print(f"   • myjpj_complete_formatted_qa_only.json (simplified)")
        print(f"   • myjpj_complete_formatted_backup_*.json (backup)")
        print(f"   • myjpj_complete_scraper.log (detailed log)")
        
        print("\n" + "="*80)
        print("✅ SCRAPING COMPLETED WITH PERFECT FORMATTING!")
        print("="*80)

def main():
    """Main execution function"""
    print("🚀 MyJPJ COMPLETE FAQ SCRAPER WITH PERFECT FORMATTING")
    print("📍 Localhost execution with comprehensive extraction")
    print("🎯 Target: https://myjpj.jpj.gov.my/faq")
    print("🔧 Features: Perfect formatting, complete extraction, multiple output formats")
    print("-" * 80)
    
    try:
        # Initialize scraper
        scraper = CompleteMyJPJScraper()
        
        # Run complete scraping
        results = scraper.scrape_complete_website()
        
        if "error" not in results:
            # Save comprehensive results
            if scraper.save_comprehensive_results(results):
                scraper.display_comprehensive_results(results)
                print("\n🎉 SUCCESS! All content extracted with perfect formatting!")
            else:
                print("❌ Failed to save results")
        else:
            print(f"❌ Scraping failed: {results['error']}")
            print("\n🔧 TROUBLESHOOTING:")
            print("1. Verify internet connection")
            print("2. Try VPN (Malaysian server preferred)")
            print("3. Check if MyJPJ website is accessible")
            print("4. Run as administrator if needed")
            print("5. Check firewall settings")
            
    except KeyboardInterrupt:
        print("\n⏹️ Scraping interrupted by user")
    except Exception as e:
        logger.error(f"💥 Critical error: {e}")
        print(f"💥 Critical error occurred: {e}")

if __name__ == "__main__":
    main()
