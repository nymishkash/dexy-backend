from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time
import logging

class WellFoundScraper:
    def __init__(self):
        self.base_url = "https://wellfound.com"
        self.logger = self._setup_logging()
        self.driver = self._setup_driver()

    def _setup_logging(self) -> logging.Logger:
        logger = logging.getLogger("WellFoundScraper")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def _setup_driver(self):
        """Setup Chrome driver with appropriate options"""
        chrome_options = Options()
        # chrome_options.add_argument('--headless')  # Uncomment to run headless
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--enable-javascript')
        # Disable automation flags
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Chrome(options=chrome_options)
        
        # Set normal browser parameters
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/119.0.0.0 Safari/537.36'
        })
        
        return driver

    def _get_next_data(self):
        """Extract __NEXT_DATA__ from the page"""
        try:
            # Wait for the next data script to be present
            script = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "__NEXT_DATA__"))
            )
            
            # Get the JSON content
            json_str = script.get_attribute('textContent')
            
            # Save for debugging
            with open('debug_next_data.json', 'w', encoding='utf-8') as f:
                f.write(json_str)
            
            return json.loads(json_str)
            
        except Exception as e:
            self.logger.error(f"Error extracting NEXT_DATA: {str(e)}")
            # Save page source for debugging
            with open('error_page.html', 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            return None

    def _extract_jobs(self, data):
        """Extract job listings from the Next.js data"""
        jobs = []
        try:
            apollo_state = data['props']['pageProps']['apolloState']['data']
            
            for key, value in apollo_state.items():
                if isinstance(value, dict) and value.get('__typename') == 'JobListing':
                    # Get company info
                    startup_ref = value.get('startup', {}).get('__ref')
                    company_info = apollo_state.get(startup_ref, {})
                    
                    job_info = {
                        'id': value.get('id'),
                        'title': value.get('title'),
                        'company': company_info.get('name'),
                        'company_logo': company_info.get('logoUrl'),
                        'location': value.get('locationNames', []),
                        'compensation': value.get('compensation'),
                        'remote': value.get('remote'),
                        'slug': value.get('slug'),
                        'raw_data': value
                    }
                    jobs.append(job_info)
            
            self.logger.info(f"Extracted {len(jobs)} jobs")
            
        except Exception as e:
            self.logger.error(f"Error extracting jobs: {str(e)}")
            
        return jobs

    def scrape_jobs(self):
        """Main scraping function"""
        try:
            url = f"{self.base_url}/jobs"
            self.logger.info(f"Fetching jobs from {url}")
            
            # Load the page
            self.driver.get(url)
            
            # Wait for page to fully load
            time.sleep(5)  # Give JavaScript time to execute
            
            # Get the data
            next_data = self._get_next_data()
            
            if not next_data:
                self.logger.error("Failed to fetch job data")
                return
            
            # Extract and save jobs
            jobs = self._extract_jobs(next_data)
            
            timestamp = int(time.time())
            filename = f'wellfound_jobs_{timestamp}.txt'
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(jobs, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved {len(jobs)} jobs to {filename}")
            return jobs
            
        finally:
            self.driver.quit()

if __name__ == "__main__":
    scraper = WellFoundScraper()
    scraper.scrape_jobs()