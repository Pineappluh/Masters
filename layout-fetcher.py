from playwright.sync_api import sync_playwright


with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("https://www.fer.unizg.hr/", wait_until="networkidle")
    page.set_viewport_size({"width": 1920, "height": 16000})

    page.screenshot(path="screenshot.png", full_page=True)

    browser.close()