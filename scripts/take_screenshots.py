import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

def main():
    # Base URL of the app
    app_url = os.environ.get("APP_URL", "http://localhost:8000")
    
    # Output directory
    output_dir = Path("screenshots")
    output_dir.mkdir(exist_ok=True)
    
    print(f"Starting screenshot capture for {app_url}...")
    
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1,
        )
        page = context.new_page()
        
        try:
            # 1. Capture Home Page
            print(f"Navigating to {app_url}...")
            page.goto(app_url, wait_until="networkidle")
            page.wait_for_timeout(1000) # extra wait for animations
            
            home_path = output_dir / "01_home.png"
            page.screenshot(path=str(home_path))
            print(f"✓ Saved home page to {home_path}")
            
            # Add additional routes to capture if desired
            # e.g., if there are specific pages described in README:
            # 2. Capture Dashboard or features page
            # page.goto(f"{app_url}/dashboard", wait_until="networkidle")
            # page.screenshot(path=str(output_dir / "02_dashboard.png"))
            
        except Exception as e:
            print(f"Error capturing screenshots: {e}", file=sys.stderr)
            print("Please ensure your app is running at the target URL.", file=sys.stderr)
        finally:
            browser.close()

if __name__ == "__main__":
    main()
