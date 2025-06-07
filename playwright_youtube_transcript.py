import asyncio
from playwright.async_api import async_playwright
import time
import os

VIDEO_URL = "https://www.youtube.com/watch?v=TifRTlamAcs"
USER_DATA_DIR = "playwright_user_data_firefox"

async def get_youtube_transcript(video_url):
    async with async_playwright() as p:
        # Use persistent context for sign-in, now with Firefox
        browser = await p.firefox.launch_persistent_context(USER_DATA_DIR, headless=False)
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

        # Scroll down further to ensure all controls are visible
        await page.evaluate("window.scrollBy(0, 1000)")
        await page.wait_for_timeout(3000)

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

        # Take a screenshot for debugging
        await page.screenshot(path="youtube_page.png")
        print("Screenshot saved as 'youtube_page.png'.")

        # Prompt for signing in if needed
        print("If you are not signed in, please sign in now. Your session will be saved for future runs.")
        print("After signing in, close the browser window to continue.")
        input("Press Enter after you have signed in and closed the browser window...")

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
                    else:
                        # If not visible, try clicking by coordinates
                        box = await btn.bounding_box()
                        if box:
                            await page.mouse.click(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
                            print(f"Clicked 'More' button {idx} by coordinates, waiting 3 seconds...")
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

        # If UI automation fails, try keyboard shortcut Shift+T
        if not transcript_clicked:
            try:
                print("Trying keyboard shortcut Shift+T to open transcript panel...")
                await page.keyboard.down('Shift')
                await page.keyboard.press('t')
                await page.keyboard.up('Shift')
                await page.wait_for_timeout(5000)
                transcript_clicked = True
            except Exception as e:
                print("Could not open transcript panel with keyboard shortcut:", e)

        # If still not interactable, try direct transcript URL
        if not transcript_clicked:
            try:
                # Construct the transcript URL
                transcript_url = f"{video_url}&t=0&transcript=1"
                await page.goto(transcript_url)
                print("Navigated to transcript URL, waiting 5 seconds...")
                await page.wait_for_timeout(5000)
                transcript_clicked = True
            except Exception as e:
                print("Could not navigate to transcript URL:", e)

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