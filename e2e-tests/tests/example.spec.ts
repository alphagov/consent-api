import { test, expect } from '@playwright/test';

test('Dummy SCON test', async ({ page }) => {
  await page.goto('http://dummy-service-1/');
  await page.getByRole('button', { name: 'Accept analytics cookies' }).click();
  await page.getByRole('link', { name: 'Cookies' }).click();
  await page.getByText('Do not use cookies that remember my settings on the site').click();
  await page.getByRole('button', { name: 'Save changes' }).click();
});
