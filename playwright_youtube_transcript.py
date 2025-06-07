import asyncio
from playwright.async_api import async_playwright
import time

VIDEO_URL = "https://www.youtube.com/watch?v=TifRTlamAcs"

async def get_youtube_transcript(video_url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(video_url)
        print("Navigated to video, waiting 5 seconds...")
        await page.wait_for_timeout(5000)

        # Dismiss any dialogs/popups (e.g., cookie consent)
        try:
            consent_btn = await page.query_selector('button:has-text("Accept")')
            if consent_btn:
                await consent_btn.click()
                print("Dismissed consent dialog.")
                await page.wait_for_timeout(1000)
        except Exception as e:
            print("No consent dialog to dismiss.")

        # Scroll down to ensure all controls are visible
        await page.evaluate("window.scrollBy(0, 500)")
        await page.wait_for_timeout(2000)

        # Dismiss overlays/popups after scrolling
        try:
            close_btn = await page.query_selector('button:has-text("Close")')
            if close_btn:
                await close_btn.click()
                print("Dismissed overlay dialog.")
                await page.wait_for_timeout(1000)
        except Exception as e:
            print("No overlay dialog to dismiss.")

        # Print all button labels for debugging, with error handling
        buttons = await page.query_selector_all('button')
        print("Button labels on the page:")
        for btn in buttons:
            try:
                label = await btn.get_attribute('aria-label')
                text = await btn.inner_text()
                print(f"aria-label: {label}, text: {text}")
            except Exception as e:
                print(f"Error reading button: {e}")

        # Try all 'More' buttons (the one that opens the menu, not the report dialog)
        more_clicked = False
        try:
            more_buttons = await page.query_selector_all('button[aria-label="More"]')
            print(f"Found {len(more_buttons)} 'More' buttons.")
            for idx, btn in enumerate(more_buttons):
                try:
                    visible = await btn.is_visible()
                    enabled = await btn.is_enabled()
                    print(f"Trying 'More' button {idx}: visible={visible}, enabled={enabled}")
                    if visible and enabled:
                        await btn.click()
                        print(f"Clicked 'More' button {idx}, waiting 3 seconds...")
                        await page.wait_for_timeout(3000)
                        more_clicked = True
                        break
                except Exception as e:
                    print(f"Error clicking 'More' button {idx}: {e}")
        except Exception as e:
            print("Could not click any 'More' button:", e)

        # After clicking 'More', look for 'Show transcript' menu item
        transcript_clicked = False
        if more_clicked:
            try:
                transcript_button = await page.wait_for_selector('ytd-menu-service-item-renderer:has-text("Show transcript")', timeout=10000)
                await transcript_button.click()
                print("Clicked 'Show transcript' from menu, waiting 5 seconds...")
                await page.wait_for_timeout(5000)
                transcript_clicked = True
            except Exception as e:
                print("Could not find/click 'Show transcript' option in menu:", e)

        # Wait for transcript panel and extract text
        try:
            transcript_panel = await page.wait_for_selector('ytd-transcript-renderer', timeout=10000)
            transcript_text = await transcript_panel.inner_text()
            print("Transcript text:")
            print(transcript_text)
        except Exception as e:
            print("Could not extract transcript:", e)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(get_youtube_transcript(VIDEO_URL)) 