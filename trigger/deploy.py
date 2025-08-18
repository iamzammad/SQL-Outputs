from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import UnexpectedAlertPresentException
import pickle
import time

COOKIE_FILE = "../login/auto_cookies.pkl"
INITIAL_EDITOR_URL = "https://www.educative.io/editor/pageeditor/6586453712175104/6204127315230720/5990508390514688"
LESSON_FILE = "../sheet/data.txt"

output_transform_code = """
function outputTransform(stdout, stderr) {
  const res_out = `
    <div style="display: flex; justify-content: center; font-family:'Inter', sans-serif;">
      <div style="overflow-y: auto;">
        <img src="/udata/WPdLXmr8eGo/QueryExecutedSuccessfully.png"
             alt="No record found, it's empty as space."
             style="max-width: 300px; height: auto; margin: auto;" />
      </div>
    </div>`;

  const apiKeys = {};
  if (!stderr) {
    if (!stdout || stdout.length === 0) {
      stdout = res_out;
    } else {
      const tblStart = `
        <link rel="stylesheet" href="https://cdn.educative.io/static/tables/modern-table.css" />
        <div class="modern-table-wrapper">
          <table class="modern-table">
      `;

      const thStart = "<th>";
      const thEnd = "</th>";
      const tdStart = "<td>";
      const tdEnd = "</td>";

      let colSt = tdStart;
      let colEnd = tdEnd;

      const rows = stdout.split(/\\r?\\n/);
      let out = tblStart;

      for (let r = 0; r < rows.length - 1; r++) {
        const cols = rows[r].split(/ ?\\t/);

        if (r == 0) {
          colSt = thStart;
          colEnd = thEnd;
          out += "<thead><tr>";
        } else if (r == 1) {
          out += "</tr></thead><tbody><tr>";
          colSt = tdStart;
          colEnd = tdEnd;
        } else {
          out += "<tr>";
        }

        for (let c = 0; c < cols.length; c++) {
          out += `${colSt}${cols[c]}${colEnd}`;
        }

        out += "</tr>";
      }

      out += "</tbody></table></div>";
      stdout = out;
    }
  }

  return { apiKeys, stdout, stderr };
}
"""

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)

def login_with_cookies():
    driver.get("https://www.educative.io")
    time.sleep(2)
    with open(COOKIE_FILE, "rb") as f:
        cookies = pickle.load(f)
    for cookie in cookies:
        cookie.pop("sameSite", None)
        cookie.pop("expiry", None)
        try:
            driver.add_cookie(cookie)
        except Exception as e:
            print(f"Error setting cookie: {e}")
    driver.get(INITIAL_EDITOR_URL)
    print("Logged in and navigated to initial editor URL.")

def handle_unexpected_alert():
    try:
        alert = driver.switch_to.alert
        print(f"Unexpected alert detected: {alert.text}")
        alert.accept()
        print("Alert accepted.")
    except Exception as e:
        print(f"Failed to handle alert: {e}")

def find_editor_link_by_lesson_name(lesson_name):
    print(f"Searching for editor link for lesson: {lesson_name}")
    try:
        elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@href, '/editor/pageeditor/') and .//span[text()]]"))
        )
        for el in elements:
            if el.text.strip() == lesson_name:
                print(f"Found lesson link: {el.get_attribute('href')}")
                return el.get_attribute("href")
        print(f"Lesson not found: {lesson_name}")
        return None
    except UnexpectedAlertPresentException:
        handle_unexpected_alert()
        return find_editor_link_by_lesson_name(lesson_name)
    except Exception as e:
        print(f"Error finding lesson link: {e}")
        return None

def go_to_edit_mode():
    max_attempts = 10
    attempt = 0
    while attempt < max_attempts:
        try:
            print("Attempting to enter Edit mode...")
            if driver.find_elements(By.XPATH, "//button[.//span[normalize-space()='Preview']]"):
                print("Already in Edit mode.")
                return
            edit_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[.//span[contains(text(), 'Edit')]]"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", edit_button)
            time.sleep(1)
            edit_button.click()
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//button[.//span[normalize-space()='Preview']]"))
            )
            print("Entered Edit mode successfully.")
            return
        except UnexpectedAlertPresentException:
            handle_unexpected_alert()
        except Exception as e:
            print(f"Edit mode attempt {attempt + 1} failed: {e}")
        attempt += 1
        time.sleep(2)
    print("Failed to enter Edit mode after multiple attempts.")

def transform_code_widgets():
    try:
        print("Waiting for code widgets to load...")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, '//button[contains(., "Run")]'))
        )
        print("Found at least one Run button.")
        run_buttons = driver.find_elements(By.XPATH, '//button[contains(., "Run")]')
        print(f"Found {len(run_buttons)} SQL code widget(s).")

        for i, run_btn in enumerate(run_buttons):
            try:
                print(f"\nProcessing widget #{i+1}")
                editable_div = run_btn.find_element(By.XPATH, '../../../../../../../../../div[1]')
                driver.execute_script("arguments[0].scrollIntoView(true);", editable_div)
                time.sleep(0.5)
                editable_div.click()
                time.sleep(1)

                html_label = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//label[span[normalize-space()='Treat Output as HTML']]"))
                )
                transform_label = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//label[span[contains(normalize-space(),'Transform Output')]]"))
                )

                # Check checkbox states using JS
                html_checked = driver.execute_script("return arguments[0].querySelector('input').checked;", html_label)
                transform_checked = driver.execute_script("return arguments[0].querySelector('input').checked;", transform_label)

                print(f"Treat Output as HTML: {'✅' if html_checked else '❌'}, Transform Output: {'✅' if transform_checked else '❌'}")

                # Skip if only Transform is checked
                if transform_checked and not html_checked:
                    print("❗ Only 'Transform Output' is checked — skipping widget to preserve API key behavior.")
                    continue

                # Ensure 'Treat Output as HTML' is checked
                if not html_checked:
                    driver.execute_script("arguments[0].scrollIntoView(true);", html_label)
                    time.sleep(0.5)
                    driver.execute_script("arguments[0].click();", html_label)
                    print("✅ Checked 'Treat Output as HTML'.")

                # If both already checked, uncheck and recheck to reopen modal
                if html_checked and transform_checked:
                    driver.execute_script("arguments[0].scrollIntoView(true);", transform_label)
                    time.sleep(0.5)
                    driver.execute_script("arguments[0].click();", transform_label)
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", transform_label)
                    print("♻️ Re-toggled 'Transform Output' to reopen modal.")
                elif not transform_checked:
                    driver.execute_script("arguments[0].scrollIntoView(true);", transform_label)
                    time.sleep(0.5)
                    driver.execute_script("arguments[0].click();", transform_label)
                    print("✅ Checked 'Transform Output'.")

                # Wait for modal and inject
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".OutputTransformModal_outputTransformModal__6RtNN .ace_editor"))
                )
                print("🪟 Transform Output modal opened.")

                js_code = f"""
                const modal = document.querySelector('.OutputTransformModal_outputTransformModal__6RtNN');
                if (modal) {{
                    const editorEl = modal.querySelector('.ace_editor');
                    if (editorEl) {{
                        const editor = ace.edit(editorEl);
                        editor.setValue({repr(output_transform_code)}, -1);
                    }}
                }}
                """
                driver.execute_script(js_code)
                print("🧠 Injected outputTransform code into modal.")

                modal = driver.find_element(By.CSS_SELECTOR, ".OutputTransformModal_outputTransformModal__6RtNN")
                modal_save_btn = WebDriverWait(modal, 10).until(
                    EC.element_to_be_clickable((By.XPATH, ".//button[contains(@class, 'outlined-default') and starts-with(normalize-space(text()), 'Save')]"))
                )
                driver.execute_script("arguments[0].scrollIntoView(true);", modal_save_btn)
                time.sleep(1)
                modal_save_btn.click()
                print("💾 Saved injected transform.")
                time.sleep(2)

            except Exception as e:
                print(f"❌ Failed to process widget #{i+1}: {e}")

    except Exception as e:
        print(f"❌ Error scanning widgets: {e}")

def save_final_lesson():
    try:
        print("Attempting to click final Save* button after processing widgets...")
        save_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'items-center')]//button[.//span[normalize-space()='Save*']]"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", save_btn)
        time.sleep(0.5)
        save_btn.click()
        print("Clicked final Save* button.")
        time.sleep(2)
    except Exception as e:
        print(f"Failed to click final Save* button: {e}")

# Main Flow
login_with_cookies()

with open(LESSON_FILE, "r", encoding="utf-8") as f:
    lines = [line.strip() for line in f if line.strip()]
    if lines:
        for i in range(len(lines)):
            current_lesson = lines[i]
            editor_url = find_editor_link_by_lesson_name(current_lesson)
            if editor_url:
                driver.get(editor_url)
                print(f"Opened: {current_lesson}")
                time.sleep(3)
                go_to_edit_mode()
                transform_code_widgets()
                save_final_lesson()
            else:
                print(f"Lesson not found in editor list: {current_lesson}")

input("Press Enter to close the browser...")
driver.quit()
