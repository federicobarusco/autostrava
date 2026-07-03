import os
import random
import time

from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth


def human_delay(min_seconds: float = 0.5, max_seconds: float = 2.0) -> None:
    """Add a random human-like delay between actions."""
    time.sleep(random.uniform(min_seconds, max_seconds))


def human_typing_delay() -> int:
    """Return a random typing delay in milliseconds."""
    return random.randint(50, 150)


class KudosGiver:
    """
    Logins into Strava and gives kudos to all activities under
    Following.
    """

    def __init__(self, max_run_duration: int = 540, headless: bool = True) -> None:
        self.EMAIL = os.environ.get("STRAVA_EMAIL")
        self.PASSWORD = os.environ.get("STRAVA_PASSWORD")
        # self.PROFILE_ID = os.environ.get("STRAVA_PROFILE_ID")

        if self.EMAIL is None or self.PASSWORD is None:
            raise Exception("Must set environ variables EMAIL and PASSWORD.")

        self.max_run_duration = max_run_duration
        self.start_time = time.time()
        self.num_entries = 100
        self.web_feed_entry_pattern = "[data-testid=web-feed-entry]"

        p = sync_playwright().start()

        # Launch Firefox with more realistic settings
        self.browser = p.firefox.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"],
        )

        # Create context with realistic viewport and user agent
        context = self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
            timezone_id="Europe/Rome",
        )

        self.page = context.new_page()

        # Apply stealth mode to hide automation signals
        Stealth().apply_stealth_sync(self.page)

    def email_login(self) -> None:
        """
        Login using email and password with human-like behavior.
        """
        base_url = os.environ.get("BASE_URL", "https://www.strava.com")
        login_url = f"{base_url}/login"

        print(f"Navigating to {login_url}...")
        self.page.goto(login_url, wait_until="networkidle")

        # Wait for page to fully load
        human_delay(1.0, 2.0)

        # Handle cookie consent
        try:
            self.page.get_by_role("button", name="Reject").click(timeout=5000)
            human_delay(0.5, 1.0)
        except Exception:
            pass

        # Type email with human-like delays
        print("Filling email...")
        email_field = self.page.get_by_role("textbox", name="email")
        email_field.click()
        human_delay(0.3, 0.7)
        email_field.type(self.EMAIL, delay=human_typing_delay())

        human_delay(0.5, 1.0)

        # Submit email first. Strava now defaults to a passwordless
        # one-time-code flow, so the password field does not exist yet.
        print("Submitting email...")
        self.page.get_by_role("button", name="Log In").click()
        human_delay(1.0, 2.0)

        # Switch back to password login, which reveals the password field.
        try:
            self.page.get_by_role("button", name="Use password instead").click(timeout=5000)
            human_delay(0.5, 1.0)
        except Exception:
            pass

        # Type password with human-like delays
        print("Filling password...")
        password_field = self.page.get_by_role("textbox", name="password")
        password_field.click()
        human_delay(0.3, 0.7)
        password_field.type(self.PASSWORD, delay=human_typing_delay())

        human_delay(0.5, 1.5)

        # Click login button
        print("Clicking login...")
        self.page.get_by_role("button", name="Log In").click()

        # Wait for navigation and check for login success
        human_delay(2.0, 4.0)

        # Check if login was successful by looking for common error indicators
        if self._check_login_success():
            print("---Logged in successfully!---")
            self._run_with_retries(func=self._get_page_and_own_profile)
        else:
            # Take a screenshot for debugging
            self.page.screenshot(path="login_failed.png")
            raise Exception("Login failed. Check login_failed.png for details.")

    def _check_login_success(self) -> bool:
        """Check if login was successful."""
        current_url = self.page.url

        # If we're redirected to dashboard or home, login succeeded
        if "dashboard" in current_url or current_url.endswith("/"):
            return True

        # Check for common error messages
        error_indicators = [
            "The username or password did not match",
            "Invalid email or password",
            "recaptcha",
            "captcha",
            "verify you're human",
        ]

        page_content = self.page.content().lower()
        for indicator in error_indicators:
            if indicator.lower() in page_content:
                print(f"Login error detected: {indicator}")
                return False

        # If still on login page, check for CAPTCHA
        if "login" in current_url:
            # Check for reCAPTCHA iframe
            captcha_frame = self.page.locator("iframe[src*='recaptcha']")
            if captcha_frame.count() > 0:
                print("CAPTCHA detected! Manual intervention required.")
                return False

        return True

    def _run_with_retries(self, func, retries=3):
        """
        Retry logic with sleep in between tries.
        """
        for i in range(retries):
            if i == retries - 1:
                raise Exception(f"Retries {retries} times failed.")
            try:
                func()
                return
            except Exception as _:
                time.sleep(1)

    def _get_page_and_own_profile(self) -> None:
        """
        Limit activities count by GET parameter and get own profile ID.
        """
        base_url = os.environ.get("BASE_URL", "https://www.strava.com")
        dashboard_url = f"{base_url}/dashboard?num_entries={self.num_entries}"

        self.page.goto(dashboard_url, wait_until="networkidle")
        human_delay(1.0, 2.0)

        # Human-like scrolling for lazy loading elements
        scroll_count = random.randint(4, 7)
        for i in range(scroll_count):
            self.page.keyboard.press("PageDown")
            human_delay(0.3, 0.8)

            # Occasionally scroll up like a human would
            if random.random() < 0.3:
                self.page.keyboard.press("PageUp")
                human_delay(0.2, 0.5)

        # Scroll back to top
        self.page.keyboard.press("Home")
        human_delay(0.5, 1.0)

        try:
            self.own_profile_id = (
                self.page.locator(".user-menu > a")
                .get_attribute("href")
                .split("/athletes/")[1]
            )
            print(f"Found profile ID: {self.own_profile_id}")
        except Exception:
            print("WARNING: Can't find own profile ID")

    def locate_kudos_buttons_and_maybe_give_kudos(self, web_feed_entry_locator) -> int:
        """
        input: playwright.locator class
        Returns count of kudos given.
        """
        w_count = web_feed_entry_locator.count()
        given_count = 0
        print(f"web feeds found: {w_count}")
        for i in range(w_count):
            # run condition check
            curr_duration = time.time() - self.start_time
            if curr_duration > self.max_run_duration:
                print("Max run duration reached.")
                break

            web_feed = web_feed_entry_locator.nth(i)
            p_count = web_feed.get_by_test_id("entry-header").count()

            # check if feed item is a club post
            if self.is_club_post(web_feed):
                print("c", end="")
                continue

            # check if activity has multiple participants
            if p_count > 1:
                for j in range(p_count):
                    participant = web_feed.get_by_test_id("entry-header").nth(j)
                    # ignore own activities
                    if not self.is_participant_me(participant):
                        kudos_container = web_feed.get_by_test_id("kudos_comments_container").nth(j)
                        button = self.find_unfilled_kudos_button(kudos_container)
                        given_count += self.click_kudos_button(unfilled_kudos_container=button)
            else:
                # ignore own activities
                if not self.is_participant_me(web_feed):
                    button = self.find_unfilled_kudos_button(web_feed)
                    given_count += self.click_kudos_button(unfilled_kudos_container=button)
        print(f"\nKudos given: {given_count}")
        return given_count

    def is_club_post(self, container) -> bool:
        """
        Returns true if the container is a club post
        """
        if container.get_by_test_id("group-header").count() > 0:
            return True

        if container.locator(".clubMemberPostHeaderLinks").count() > 0:
            return True

        return False

    def is_participant_me(self, container) -> bool:
        """
        Returns true is the container's owner is logged-in user.
        """
        owner = self.own_profile_id
        try:
            h = container.get_by_test_id("owners-name").get_attribute("href")
            hl = h.split("/athletes/")
            owner = hl[1]
        except Exception as _:
            print("Some issue with getting owners-name container.")
        return owner == self.own_profile_id

    def find_unfilled_kudos_button(self, container):
        """
        Returns button as a playwright.locator class
        """
        button = None
        try:
            button = container.get_by_test_id("unfilled_kudos")
        except Exception as _:
            print("Some issue with finding the unfilled_kudos container.")
        return button

    def click_kudos_button(self, unfilled_kudos_container) -> int:  # type: ignore[no-untyped-def]
        """
        input: playwright.locator class
        Returns 1 if kudos button was clicked else 0
        """
        if unfilled_kudos_container.count() == 1:
            # Add human-like delay before clicking
            human_delay(0.2, 0.5)
            unfilled_kudos_container.click(timeout=5000)
            print("=", end="", flush=True)
            # Variable delay between kudos (humans aren't perfectly consistent)
            human_delay(0.8, 2.0)
            return 1
        return 0

    def give_kudos(self):
        """
        Interate over web feed entries
        """
        ## Give Kudos on loaded page ##
        try:
            self.page.get_by_role("button", name="Accept").click(timeout=5000)
            print("Accepting updated terms.")
        except Exception as _:
            pass
        web_feed_entry_locator = self.page.locator(self.web_feed_entry_pattern)
        self.locate_kudos_buttons_and_maybe_give_kudos(web_feed_entry_locator=web_feed_entry_locator)
        self.browser.close()


def main(headless: bool = True) -> None:
    """
    Main entry point for the kudos giver.

    Args:
        headless: If False, browser will be visible (useful for debugging).
    """
    # Check for debug mode via environment variable
    debug_mode = os.environ.get("AUTOSTRAVA_DEBUG", "").lower() in ("1", "true", "yes")
    if debug_mode:
        headless = False
        print("Running in DEBUG mode (browser visible)")

    kg = KudosGiver(headless=headless)
    kg.email_login()
    kg.give_kudos()


if __name__ == "__main__":
    main()
