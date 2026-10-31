import asyncio, sys
from playwright.async_api import async_playwright

URL = "http://localhost:8599/"
TABS = ["Summary", "Equipment ratings", "Checks", "Cables & busway", "PUE & energy", "vs phase 1"]


async def main(out="docs/screenshots"):
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width": 1600, "height": 2000}, device_scale_factor=1)
        await pg.goto(URL)
        await pg.wait_for_selector("text=Campus demand", timeout=60000)
        await pg.wait_for_timeout(4000)
        for i, t in enumerate(TABS, 1):
            await pg.get_by_role("tab", name=t).click()
            await pg.wait_for_timeout(2500)
            await pg.screenshot(path=f"{out}/app_{i:02d}_{t.split()[0].lower().replace('&','')}.png", full_page=True)
        exc = await pg.locator("[data-testid='stException']").count()
        print("exceptions on page:", exc)
        await b.close()

asyncio.run(main(*sys.argv[1:]))
