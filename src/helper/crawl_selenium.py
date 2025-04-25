from bs4 import BeautifulSoup
import requests
import re
import json
import time
import random
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from helper.handleCaptcha import solve_captcha
import gc

HEADERS = {
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
    'Accept-Language': 'vi,en-US;q=0.9,en;q=0.8',
    'accept-encoding': 'gzip, deflate, br, zstd',
    'referer': 'https://www.amazon.com/',
    'accept': '*/*'
}

def extract_product_id(url):
    """
    Trích xuất ProductID từ URL Amazon
    
    Args:
        url (str): URL của sản phẩm Amazon
        
    Returns:
        str: ProductID hoặc None nếu không tìm thấy
    """
    # Các pattern phổ biến để tìm product ID trong URL Amazon:
    patterns = [
        r'/dp/([A-Z0-9]{10})/?',       # /dp/B00EXAMPLE/
        r'/gp/product/([A-Z0-9]{10})/?',  # /gp/product/B00EXAMPLE/
        r'/ASIN/([A-Z0-9]{10})/?',     # /ASIN/B00EXAMPLE/
        r'product/([A-Z0-9]{10})/?',    # product/B00EXAMPLE
        r'product-reviews/([A-Z0-9]{10})/?'  # product-reviews/B00EXAMPLE/
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def is_product_id_in_list(product_id):
    """
    Kiểm tra xem ProductID có trong danh sách unique_product_ids.txt không
    
    Args:
        product_id (str): ID sản phẩm cần kiểm tra
        
    Returns:
        bool: True nếu ID có trong danh sách, False nếu không
    """
    if not product_id:
        return False
        
    # Đường dẫn đến file unique_product_ids.txt
    file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                           'data', 'unique_product_ids.txt')
    
    try:
        with open(file_path, 'r') as file:
            product_ids = file.read().splitlines()
            return product_id in product_ids
    except Exception as e:
        print(f"Lỗi khi đọc file unique_product_ids.txt: {str(e)}")
        return False

def setup_driver(headless=True):  # Default to headless mode
    """Setup and return a Chrome webdriver with appropriate options"""
    chrome_options = Options()
    
    # Always run headless in Docker environment
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration
    chrome_options.add_argument("--no-sandbox")  # Required in Docker
    chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource
    chrome_options.add_argument("--disable-extensions")  # Disable extensions
    chrome_options.add_argument("--disable-setuid-sandbox")  # Disable setuid sandbox
    chrome_options.add_argument(f"user-agent={HEADERS['User-Agent']}")
    
    # Add some preferences that make detection harder
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    try:
        # Check if running in a Docker environment - use installed chromedriver
        if os.path.exists("/.dockerenv"):
            print("Running in Docker environment, using installed chromedriver")
            driver = webdriver.Chrome(options=chrome_options)
        else:
            # Use webdriver-manager to handle driver installation for local development
            print("Running in local environment, using webdriver-manager")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        print(f"Error setting up Chrome driver: {e}")
        # Fallback to direct path in Docker
        print("Falling back to direct chromedriver path")
        driver = webdriver.Chrome(executable_path="/usr/bin/chromedriver", options=chrome_options)
    
    # Set window size to typical desktop
    driver.set_window_size(1920, 1080)
    return driver

def get_product_info(url):
    """Extract basic product information from an Amazon product page using Selenium"""
    driver = setup_driver(headless=True)
    try:
        driver.get(url)
        time.sleep(random.uniform(3, 5))  # Random delay to mimic human behavior
        
        # Check if we hit a CAPTCHA and try to solve it
        if solve_captcha(driver):
            print("🔄 Continuing after captcha solution...")
            time.sleep(3)  # Wait a bit for the page to fully load

        # Product dictionary to store all information
        product = {}
        
        # Get product title
        try:
            title_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "productTitle"))
            )
            product["title"] = title_element.text.strip()
        except:
            product["title"] = "Title not found"
        
        # Get product price
        try:
            price_element = driver.find_element(By.CSS_SELECTOR, ".a-offscreen")
            product["price"] = price_element.get_attribute("innerText")
        except:
            product["price"] = "Price not found"
        
        # Get product rating
        try:
            rating_element = driver.find_element(By.CSS_SELECTOR, ".a-icon-alt")
            product["rating"] = rating_element.get_attribute("innerText")
        except:
            product["rating"] = "Rating not found"
        
        # Get number of reviews
        try:
            review_count_element = driver.find_element(By.ID, "acrCustomerReviewText")
            product["review_count"] = review_count_element.text
        except:
            product["review_count"] = "Review count not found"
        
        # Get product description
        try:
            description_element = driver.find_element(By.ID, "feature-bullets")
            product["description"] = description_element.text
        except:
            product["description"] = "Description not found"

        # Get any information from table (if available) <table class="a-normal a-spacing-micro">
        try:
            product["table"] = {}  # Initialize the table dictionary
            table_element = driver.find_element(By.CSS_SELECTOR, ".a-normal.a-spacing-micro")
            table_rows = table_element.find_elements(By.TAG_NAME, "tr")
            for row in table_rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) == 2:
                    key = cells[0].text.strip()
                    value = cells[1].text.strip()
                    product["table"][key] = value
        except:
            product["table"] = {}  # Ensure table key exists even if there's an error
        
        # Get product images
        try:
            img_element = driver.find_element(By.ID, "landingImage")
            img_data = img_element.get_attribute('data-a-dynamic-image')
            if img_data:
                img_urls = json.loads(img_data)
                product["images"] = list(img_urls.keys())
            else:
                product["images"] = [img_element.get_attribute('src')]
        except:
            product["images"] = []

        # Get reviews <li id="" data-hook="review" class="review aok-relative">
        try:
            product["reviews"] = []  # Initialize the reviews list
            review_elements = driver.find_elements(By.CSS_SELECTOR, "li.review")
            print(f"Found {len(review_elements)} reviews")
            for review in review_elements:
                review_dict = {}
                # review_dict["title"] = review.find_element(By.CSS_SELECTOR, "a[data-hook='review-title']").text.strip()
                # review_dict["rating"] = review.find_element(By.CSS_SELECTOR, "i[data-hook='review-star-rating']").text.strip()
                # review_dict["text"] = review.find_element(By.CSS_SELECTOR, "span[data-hook='review-body']").text.strip()
                # review_dict["author"] = review.find_element(By.CSS_SELECTOR, "span.a-profile-name").text.strip()
                # review_dict["date"] = review.find_element(By.CSS_SELECTOR, "span[data-hook='review-date']").text.strip()
                # product["reviews"].append(review_dict)

                # For the review title
                try:
                    # Try first with anchor tag (original reviews)
                    try:
                        title_element = review.find_element(By.CSS_SELECTOR, "a[data-hook='review-title']")
                        review_dict["title"] = title_element.text.strip()
                    except:
                        # If not found, try with span (reviews from other countries)
                        title_element = review.find_element(By.CSS_SELECTOR, "span[data-hook='review-title']")
                        review_dict["title"] = title_element.text.strip()
                except:
                    review_dict["title"] = "No title"

                # For the review text
                try:
                    text_element = review.find_element(By.CSS_SELECTOR, "span[data-hook='review-body']")
                    review_dict["text"] = text_element.text.strip()
                except:
                    review_dict["text"] = "No review text"
                
                # For the author
                try:
                    author_element = review.find_element(By.CSS_SELECTOR, "span.a-profile-name")
                    review_dict["author"] = author_element.text.strip()
                except:
                    review_dict["author"] = "Anonymous"
                
                # For the review date
                try:
                    date_element = review.find_element(By.CSS_SELECTOR, "span[data-hook='review-date']")
                    review_dict["date"] = date_element.text.strip()
                except:
                    review_dict["date"] = "No date"

                product["reviews"].append(review_dict)
        except Exception as e:
            print(f"Error parsing reviews: {str(e)}")
            product["reviews"] = []  # Ensure reviews key exists even if there's an error
        
        return product
    except Exception as e:
        return {"error": str(e)}
    finally:
        driver.quit()  # Close the browser
        del driver  # Explicitly delete the driver object
        gc.collect()

def get_basic_product_info(url):
    """Extract only basic product information (title, price, rating, description) from an Amazon product page"""
    max_retries = 2
    for attempt in range(max_retries):
        driver = None
        try:
            print(f"Attempt {attempt+1}: Getting basic product info for {url}")
            driver = setup_driver(headless=True)
            driver.get(url)
            
            # Tăng thời gian chờ trong môi trường Docker
            wait_time = 5 if os.path.exists("/.dockerenv") else 3
            time.sleep(random.uniform(wait_time, wait_time + 2))
            
            # Xử lý CAPTCHA nếu xuất hiện
            if solve_captcha(driver):
                print("🔄 Continuing after captcha solution...")
                time.sleep(3)  # Tăng thời gian chờ sau khi giải captcha

            # Bộ từ điển chỉ chứa thông tin cơ bản
            product = {}
            
            # Thêm WebDriverWait để đảm bảo các element đã load
            wait = WebDriverWait(driver, 15)  # Tăng timeout lên 15 giây
            
            # Lấy tiêu đề sản phẩm
            try:
                title_element = wait.until(EC.presence_of_element_located((By.ID, "productTitle")))
                product["title"] = title_element.text.strip()
                print(f"Found title: {product['title'][:30]}...")
            except Exception as e:
                print(f"Title error: {e}")
                product["title"] = "Title not found"
            
            # Lấy giá sản phẩm với wait
            try:
                price_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".a-offscreen")))
                product["price"] = price_element.get_attribute("innerText")
                print(f"Found price: {product['price']}")
            except Exception as e:
                print(f"Price error: {e}")
                product["price"] = "Price not found"
            
            # Các phần còn lại tương tự...
            
            # Kiểm tra xem đã lấy được thông tin cơ bản chưa
            if product.get("title") != "Title not found":
                print("Successfully retrieved basic product info")
                return product
                
            # Nếu attempt đầu tiên không thành công, thử lần nữa
            if attempt < max_retries - 1:
                print("First attempt failed, will retry...")
                time.sleep(2)  # Đợi trước khi thử lại
                
        except Exception as e:
            print(f"Error in get_basic_product_info (attempt {attempt+1}): {str(e)}")
            if attempt < max_retries - 1:
                print("Retrying after error...")
                time.sleep(2)
        finally:
            if driver:
                driver.quit()
                del driver
                gc.collect()
    
    return {"error": "Failed after retries", "title": "Error retrieving product", "price": "Unknown", 
            "rating": "Not available", "description": "Failed to load product information"}