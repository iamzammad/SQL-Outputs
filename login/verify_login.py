from selenium import webdriver
import pickle
import time

COOKIE_FILE = "educative_cookies.pkl"

# Start WebDriver
driver = webdriver.Chrome()

def login_with_cookies():
    driver.get("https://www.educative.io")
    time.sleep(2)

    # Load cookies from file
    with open(COOKIE_FILE, "rb") as f:
        cookies = pickle.load(f)

    # Set cookies in the browser
    for cookie in cookies:
        # Adjust domain if needed
        if "sameSite" in cookie:
            del cookie["sameSite"]
        driver.add_cookie(cookie)

    # Reload to apply cookies
    driver.get("https://www.educative.io")
    # time.sleep(3)
    print("Logged in using cookies.")
    input("Press Enter to close the browser...")
    driver.quit()


# Run login
login_with_cookies()