import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

def debug_jpj_access():
    url = "https://myjpj.jpj.gov.my/faq"
    
    print("=== JPJ Website Access Debug Tool ===\n")
    
    # Test 1: Basic requests
    print("1. Testing with Python requests...")
    session = requests.Session()
    
    headers_to_test = [
        # Default requests header
        {},
        # Basic browser headers
        {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        },
        # Full browser headers
        {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,ms;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://www.google.com/'
        }
    ]
    
    for i, headers in enumerate(headers_to_test, 1):
        try:
            response = session.get(url, headers=headers, timeout=10)
            print(f"  Test {i}: Status {response.status_code}")
            
            if response.status_code == 200:
                print(f"    ✓ Success! Content length: {len(response.text)} chars")
                if 'faq' in response.text.lower():
                    print("    ✓ FAQ content detected")
                else:
                    print("    ⚠ No FAQ content detected in response")
            elif response.status_code == 403:
                print("    ✗ Forbidden - likely blocked by WAF")
            elif response.status_code == 503:
                print("    ✗ Service unavailable - possible Cloudflare protection")
            elif response.status_code in [301, 302]:
                print(f"    → Redirected to: {response.headers.get('Location', 'Unknown')}")
            else:
                print(f"    ? Unexpected status: {response.status_code}")
                
        except requests.exceptions.SSLError:
            print(f"  Test {i}: SSL Error - try with verify=False")
        except requests.exceptions.Timeout:
            print(f"  Test {i}: Timeout - server might be slow")
        except requests.exceptions.ConnectionError:
            print(f"  Test {i}: Connection Error - check internet/DNS")
        except Exception as e:
            print(f"  Test {i}: Error - {e}")
    
    # Test 2: Selenium access
    print("\n2. Testing with Selenium...")
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(20)
        
        print("  Loading page with Selenium...")
        start_time = time.time()
        driver.get(url)
        load_time = time.time() - start_time
        
        print(f"  Page loaded in {load_time:.2f} seconds")
        print(f"  Current URL: {driver.current_url}")
        print(f"  Page title: {driver.title}")
        
        # Check for blocking indicators
        page_source = driver.page_source.lower()
        blocking_indicators = {
            'cloudflare': 'cloudflare' in page_source,
            'captcha': 'captcha' in page_source,
            'access_denied': 'access denied' in page_source,
            'blocked': 'blocked' in page_source or 'block' in page_source,
            'bot_detection': 'bot' in page_source and 'detect' in page_source,
            'ray_id': 'ray id' in page_source
        }
        
        detected_blocks = [k for k, v in blocking_indicators.items() if v]
        if detected_blocks:
            print(f"  ⚠ Detected blocking mechanisms: {', '.join(detected_blocks)}")
        else:
            print("  ✓ No obvious blocking detected")
        
        # Check for FAQ content
        if 'faq' in page_source:
            print("  ✓ FAQ content detected")
            
            # Look for accordion elements
            accordion_selectors = [
                '[data-bs-toggle="collapse"]',
                '.accordion-button',
                '.faq-question',
                '.collapse-toggle'
            ]
            
            for selector in accordion_selectors:
                elements = driver.find_elements("css selector", selector)
                if elements:
                    print(f"    Found {len(elements)} elements with selector: {selector}")
        else:
            print("  ✗ No FAQ content detected")
        
        # Save page source for manual inspection
        with open('jpj_page_source.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("  💾 Page source saved to 'jpj_page_source.html'")
        
        driver.quit()
        
    except Exception as e:
        print(f"  ✗ Selenium error: {e}")
    
    # Test 3: Alternative URLs
    print("\n3. Testing alternative JPJ URLs...")
    alternative_urls = [
        "https://www.jpj.gov.my/",
        "https://myjpj.jpj.gov.my/",
        "https://myjpj.jpj.gov.my/web/main-site/home",
    ]
    
    for alt_url in alternative_urls:
        try:
            response = requests.get(alt_url, timeout=5, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            print(f"  {alt_url}: Status {response.status_code}")
        except Exception as e:
            print(f"  {alt_url}: Error - {e}")
    
    print("\n=== Recommendations ===")
    print("1. Check 'jpj_page_source.html' to see what content is actually returned")
    print("2. If you see Cloudflare or bot detection, try:")
    print("   - Using undetected-chromedriver")
    print("   - Adding longer delays between requests")
    print("   - Using a VPN with Malaysian IP")
    print("3. If the page loads but has different structure, update the selectors")
    print("4. Consider contacting JPJ for API access if available")

if __name__ == "__main__":
    debug_jpj_access()