"""Full-page screenshots of every tab (needs `streamlit run app.py --server.port 8599` running)."""
import asyncio
import sys

from playwright.async_api import async_playwright

URL = "http://localhost:8599/"
TABS = ["Overview", "Peak shaving", "Backup role", "Revenue stacking", "AI smoothing", "Business case",
        "Assumptions & sources"]


async def main(out="docs/screenshots"):
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width": 1600, "height": 1800}, device_scale_factor=1)
        await pg.goto(URL)
        await pg.wait_for_selector("text=Extra IT under limit", timeout=120000)
        await pg.wait_for_timeout(5000)
        for i, t in enumerate(TABS, 1):
            await pg.get_by_role("tab", name=t).click()
            await pg.wait_for_timeout(3000)
            name = t.split()[0].lower().replace("&", "")
            await pg.screenshot(path=f"{out}/app_{i:02d}_{name}.png", full_page=True)
        exc = await pg.locator("[data-testid='stException']").count()
        print("exceptions on page:", exc)
        await b.close()

asyncio.run(main(*sys.argv[1:]))
