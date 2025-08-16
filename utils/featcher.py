from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
import requests

def fetch_html_selenium(url: str) -> str:
    # Try fallback using requests
    try:
        response = requests.get(url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0"
        })
        if response.status_code == 200:
            print("✅ HTML fetched successfully via requests fallback")
            return response.text
        else:
            print(f"⚠️ requests.get() failed with status {response.status_code}")
    except Exception as fallback_error:
        print(f"❌ requests fallback failed: {fallback_error}")
    
    return ""
