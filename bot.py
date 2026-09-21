from pathlib import Path
import json
from datetime import datetime

from playwright.sync_api import sync_playwright


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)


# ============================================================
# LOAD CONFIG
# ============================================================

form_url = (
    BASE_DIR / "form_url.txt"
).read_text(encoding="utf-8").strip().strip('"').strip("'")


with open(BASE_DIR / "config.json", "r", encoding="utf-8") as f:
    config = json.load(f)


# ============================================================
# LOGGING
# ============================================================

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_file = LOG_DIR / f"submission_{timestamp}.txt"


def log(message):
    print(message)

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(message + "\n")


# ============================================================
# VALIDATE URL
# ============================================================

if not form_url.startswith("https://docs.google.com/forms/"):
    log("ERROR: Invalid Google Forms URL.")
    raise SystemExit(1)


# ============================================================
# START
# ============================================================

log("=" * 60)
log("ROTI AUTOMATION STARTED")
log("=" * 60)

log(f"Time: {datetime.now()}")
log(f"Form: {form_url}")


# ============================================================
# PLAYWRIGHT
# ============================================================

with sync_playwright() as p:

    browser = p.chromium.launch(
        headless=True
    )

    page = browser.new_page(
        viewport={
            "width": 1280,
            "height": 900
        }
    )

    try:

        # ----------------------------------------------------
        # OPEN FORM
        # ----------------------------------------------------

        log("Opening Google Form...")

        page.goto(
            form_url,
            wait_until="domcontentloaded",
            timeout=30000
        )

        page.wait_for_timeout(3000)

        log(f"Form title: {page.title()}")


        # ----------------------------------------------------
        # FILL NAME
        # ----------------------------------------------------

        log("Filling Name...")

        name_field = page.get_by_text(
            "Name:",
            exact=True
        ).locator(
            "xpath=following::input[1]"
        )

        name_field.fill(
            config["name"]
        )


        # ----------------------------------------------------
        # SELECT ROTI
        # ----------------------------------------------------

        log("Selecting Roti = Yes...")

        page.get_by_text(
            config["roti"],
            exact=True
        ).first.click()


        # ----------------------------------------------------
        # FILL ROOM NUMBER
        # ----------------------------------------------------

        log("Filling Room Number...")

        room_field = page.get_by_text(
            "Room Number",
            exact=True
        ).locator(
            "xpath=following::input[1]"
        )

        room_field.fill(
            config["room_number"]
        )


        # ----------------------------------------------------
        # SUBMIT
        # ----------------------------------------------------

        log("Submitting form...")

        page.get_by_role(
            "button",
            name="Submit"
        ).click()

        page.wait_for_timeout(4000)


        # ----------------------------------------------------
        # CHECK RESULT
        # ----------------------------------------------------

        current_url = page.url

        body_text = page.locator(
            "body"
        ).inner_text()

        body_lower = body_text.lower()

        log(f"URL after submission: {current_url}")

        log("Checking submission confirmation...")


        success_messages = [
            "your response has been recorded",
            "response has been recorded",
            "response recorded",
            "thanks for submitting",
            "your response was recorded",
            "response was recorded"
        ]


        submitted = any(
            message in body_lower
            for message in success_messages
        )


        if submitted:

            log("=" * 60)
            log("SUCCESS: FORM SUBMITTED")
            log("=" * 60)

        else:

            log("=" * 60)
            log("WARNING: SUBMISSION STATUS UNCLEAR")
            log("=" * 60)

            log("Page URL:")
            log(current_url)

            log("Page text:")
            log(body_text[:3000])

            screenshot = BASE_DIR / "submission_result.png"

            page.screenshot(
                path=str(screenshot),
                full_page=True
            )

            log(
                f"Screenshot saved: {screenshot}"
            )

            raise RuntimeError(
                "Could not confirm form submission."
            )


    except Exception as e:

        log("=" * 60)
        log("ERROR DURING SUBMISSION")
        log("=" * 60)

        log(str(e))


        try:

            screenshot = BASE_DIR / "error.png"

            page.screenshot(
                path=str(screenshot),
                full_page=True
            )

            log(
                f"Error screenshot saved: {screenshot}"
            )

        except Exception:
            pass


        raise


    finally:

        browser.close()


log("Automation finished.")
