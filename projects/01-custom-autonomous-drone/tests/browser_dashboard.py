"""Exercise the local dashboard in parallel browser viewports."""
import argparse
import asyncio
import json
import os
from pathlib import Path
from playwright.async_api import async_playwright

async def run(base_url, output):
    output.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as playwright:
        executable = os.environ.get('BROWSER_EXECUTABLE')
        options = {'headless': True}
        if executable:
            options['executable_path'] = executable
        browser = await playwright.chromium.launch(**options)
        async def check(name, width, height):
            page = await browser.new_page(viewport={'width': width, 'height': height})
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            try:
                await page.goto(base_url, wait_until='networkidle')
                await page.locator('#scenario:not([disabled])').wait_for()
                if '3 times 3.7 V = 11.10 V' not in await page.locator('#formula-nominal').inner_text():
                    raise AssertionError('Nominal voltage formula is incorrect')
                if '3 times 4.2 V = 12.60 V' not in await page.locator('#formula-full').inner_text():
                    raise AssertionError('Full charge reference is incorrect')
                if await page.locator('#battery-power').inner_text() != '88.80 W':
                    raise AssertionError('Power is incorrect')
                await page.locator('#step').fill('200')
                if await page.locator('#battery-used').inner_text() != '22.22 mAh':
                    raise AssertionError('Charge calculation is incorrect')
                if await page.locator('#battery-energy').inner_text() != '0.2467 Wh':
                    raise AssertionError('Energy calculation is incorrect')
                if 'squared divided by' not in await page.locator('#formula-gain').inner_text():
                    raise AssertionError('Filter calculation is missing')
                response = await page.request.get(base_url.rstrip('/') + '/api/scenarios')
                baseline = (await response.json())[0]
                sample = baseline['report']['trace'][200]
                control = sample['control']
                update = sample['updates']['pressure']
                if f"{control['unclamped_thrust_n']:.2f} N" not in await page.locator('#formula-thrust').inner_text():
                    raise AssertionError('Displayed thrust does not match the trace')
                if f"{update['normalised_innovation_squared']:.4f}" not in await page.locator('#formula-gain').inner_text():
                    raise AssertionError('Displayed innovation does not match the trace')
                await page.select_option('#scenario', 'position_outage')
                await page.locator('#step').fill('105')
                if 'not a flight safety procedure' not in (await page.locator('#formula-clamp').inner_text()).lower():
                    raise AssertionError('Degraded state is not explained')
                if await page.locator('#step-label').inner_text() != '106 / 300':
                    raise AssertionError('Playback position did not update')
                if not await page.evaluate('document.documentElement.scrollWidth <= innerWidth'):
                    raise AssertionError('Page overflows the viewport')
                async with page.expect_download() as info:
                    await page.get_by_role('button', name='Download run data').click()
                download = await info.value
                data = json.loads(Path(await download.path()).read_text(encoding='utf-8'))
                if data['battery_example']['cells_in_series'] != 3:
                    raise AssertionError('Downloaded battery example is not three cell')
                await page.screenshot(path=str(output / f'{name}.png'), full_page=True)
                if errors:
                    raise AssertionError(f'Browser errors: {errors}')
                print(f'{name}: passed')
            finally:
                await page.close()
        try:
            await asyncio.gather(check('desktop', 1440, 900), check('tablet', 768, 1024), check('phone', 320, 680))
        finally:
            await browser.close()

def main():
    parser = argparse.ArgumentParser(description='Check the local synthetic dashboard')
    parser.add_argument('--url', default='http://127.0.0.1:8766/')
    parser.add_argument('--output', default='results/browser')
    args = parser.parse_args()
    asyncio.run(run(args.url, Path(args.output)))

if __name__ == '__main__':
    main()
