import pytest

pytest.importorskip("selenium")

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait


# =========================
# Authentication smoke tests
# =========================

def test_user_can_register_and_login(browser, live_server):
    register_user(browser, live_server, "seleniumuser", "selenium@example.com")
    login_user(browser, live_server, "seleniumuser", open_studybuddy=False)

    assert "Welcome back" in browser.page_source
    assert "/home" in browser.current_url


def test_invalid_login_stays_on_login_page(browser, live_server):
    wait = WebDriverWait(browser, 5)

    browser.get(f"{live_server}/login")
    browser.find_element(By.ID, "login-identifier").send_keys("student")
    browser.find_element(By.ID, "login-password").send_keys("wrongpassword")
    browser.find_element(By.CSS_SELECTOR, ".auth-submit").click()

    wait.until(EC.url_contains("/login"))

    assert "/login" in browser.current_url
    assert "Log In" in browser.page_source


def test_logout_returns_user_to_login_page(browser, live_server):
    login_user(browser, live_server, open_studybuddy=False)

    wait = WebDriverWait(browser, 5)

    browser.find_element(By.ID, "profileToggle").click()
    wait.until(EC.visibility_of_element_located((By.ID, "profileMenu")))

    browser.find_element(By.CSS_SELECTOR, ".profile-menu-form button").click()

    wait.until(EC.url_contains("/login"))
    wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "Log In"))

    assert "Log In" in browser.page_source
    assert "/login" in browser.current_url


# =========================
# Study Buddy smoke test
# =========================

def test_session_detail_allows_joined_user_to_post_message(browser, live_server):
    login_user(browser, live_server)

    browser.get(f"{live_server}/studybuddy")
    browser.find_element(By.XPATH, "//button[normalize-space()='Join Session']").click()

    wait = WebDriverWait(browser, 5)

    message_input = wait.until(
        EC.visibility_of_element_located(
            (By.CSS_SELECTOR, ".message-form textarea[name='content']")
        )
    )

    browser.execute_script(
        "arguments[0].value = arguments[1];",
        message_input,
        "Selenium discussion question",
    )

    browser.find_element(By.CSS_SELECTOR, ".message-form").submit()

    wait.until(
        EC.text_to_be_present_in_element(
            (By.TAG_NAME, "body"),
            "Selenium discussion question",
        )
    )

    assert "Selenium discussion question" in browser.page_source


# =========================
# Forum smoke tests
# =========================

def test_user_can_create_forum_thread(browser, live_server):
    wait = WebDriverWait(browser, 5)

    login_user(browser, live_server, open_studybuddy=False)

    create_forum_thread(
        browser,
        live_server,
        title="Selenium Forum Thread",
        body="This forum thread was created by a Selenium test.",
        category="Web Development",
    )

    wait.until(
        EC.text_to_be_present_in_element(
            (By.TAG_NAME, "body"),
            "Selenium Forum Thread",
        )
    )

    assert "Selenium Forum Thread" in browser.page_source
    assert "This forum thread was created by a Selenium test." in browser.page_source
    assert "Web Development" in browser.page_source


def test_user_can_like_and_save_forum_thread(browser, live_server):
    wait = WebDriverWait(browser, 5)

    login_user(browser, live_server, open_studybuddy=False)

    create_forum_thread(
        browser,
        live_server,
        title="Selenium Like Save Forum Thread",
        body="This thread is used to test forum like and save buttons.",
        category="General",
    )

    browser.get(f"{live_server}/forum?sort=new")

    wait.until(
        EC.text_to_be_present_in_element(
            (By.TAG_NAME, "body"),
            "Selenium Like Save Forum Thread",
        )
    )

    thread_card = browser.find_element(
        By.XPATH,
        "//article[contains(@class, 'thread-card') and .//*[contains(text(), 'Selenium Like Save Forum Thread')]]",
    )

    like_button = thread_card.find_element(By.CSS_SELECTOR, "[data-like-thread]")
    save_button = thread_card.find_element(By.CSS_SELECTOR, "[data-save-thread]")

    original_like_state = like_button.get_attribute("aria-pressed")
    original_save_state = save_button.get_attribute("aria-pressed")

    browser.execute_script("arguments[0].click();", like_button)

    wait.until(
        lambda driver: like_button.get_attribute("aria-pressed") != original_like_state
    )

    assert like_button.get_attribute("aria-pressed") != original_like_state

    browser.execute_script("arguments[0].click();", save_button)

    wait.until(
        lambda driver: save_button.get_attribute("aria-pressed") != original_save_state
    )

    assert save_button.get_attribute("aria-pressed") != original_save_state


# =========================
# Helpers
# =========================

def register_user(browser, live_server, username, email):
    wait = WebDriverWait(browser, 5)

    browser.get(f"{live_server}/register")

    browser.find_element(By.ID, "register-username").send_keys(username)
    browser.find_element(By.ID, "register-email").send_keys(email)
    browser.find_element(By.ID, "register-password").send_keys("Password1")
    browser.find_element(By.ID, "confirm-password").send_keys("Password1")

    browser.find_element(By.CSS_SELECTOR, ".auth-submit").click()

    wait.until(EC.url_contains("/login"))


def login_user(
    browser,
    live_server,
    identifier="student",
    password="Password1",
    open_studybuddy=True,
):
    wait = WebDriverWait(browser, 5)

    browser.get(f"{live_server}/login")

    browser.find_element(By.ID, "login-identifier").send_keys(identifier)
    browser.find_element(By.ID, "login-password").send_keys(password)

    browser.find_element(By.CSS_SELECTOR, ".auth-submit").click()

    wait.until(EC.url_contains("/home"))

    if open_studybuddy:
        browser.get(f"{live_server}/studybuddy")
        wait.until(EC.presence_of_element_located((By.ID, "openCreateModal")))


def create_forum_thread(browser, live_server, title, body, category="General"):
    wait = WebDriverWait(browser, 8)

    browser.get(f"{live_server}/forum")

    open_button = wait.until(
        EC.element_to_be_clickable((By.ID, "openCreateThreadPanel"))
    )
    open_button.click()

    wait.until(
        lambda driver: driver.find_element(By.ID, "createThreadPanel")
        .get_attribute("aria-hidden") == "false"
    )

    category_select = wait.until(
        EC.element_to_be_clickable((By.ID, "thread-category"))
    )
    Select(category_select).select_by_visible_text(category)

    title_input = wait.until(
        EC.element_to_be_clickable((By.ID, "thread-title"))
    )

    browser.execute_script(
        "arguments[0].scrollIntoView({block: 'center'});",
        title_input,
    )

    title_input.click()
    title_input.clear()
    title_input.send_keys(title)

    wait.until(
        lambda driver: driver.find_element(By.ID, "thread-title")
        .get_attribute("value") == title
    )

    body_input = wait.until(
        EC.element_to_be_clickable((By.ID, "thread-body"))
    )

    body_input.click()
    body_input.clear()
    body_input.send_keys(body)

    wait.until(
        lambda driver: driver.find_element(By.ID, "thread-body")
        .get_attribute("value") == body
    )

    submit_button = wait.until(
        EC.element_to_be_clickable((By.ID, "submit-thread-button"))
    )
    submit_button.click()

    wait.until(
        EC.text_to_be_present_in_element((By.TAG_NAME, "body"), title)
    )