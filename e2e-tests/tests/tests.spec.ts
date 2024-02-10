import { test, expect } from '@playwright/test';
import {assertCookie, clearCookies} from './utils';

const serviceOneOrigin = process.env.DUMMY_SERVICE_1_ORIGIN || 'http://localhost:8001';
const serviceTwoOrigin = process.env.DUMMY_SERVICE_2_ORIGIN || 'http://localhost:8002';





test('I can manage the cookies on a single domain, starting with a rejection', async ({ page }) => {
  await page.goto(`${serviceOneOrigin}/dummy-service/`);
  await clearCookies(page)
  await expect(page.getByLabel('Cookies on GOV.UK')).toBeVisible();
  await page.getByRole('button', { name: 'Reject analytics cookies' }).click();

  await expect(page.getByLabel('Cookies on GOV.UK')).not.toBeVisible();

  await assertCookie(page, 'cookies_policy', { usage: false, settings: false, essential: true, campaigns:false });
  await assertCookie(page, 'cookies_preferences_set', 'true');
  await assertCookie(page, 'gov_singleconsent_uid',);


  await page.getByRole('link', { name: 'Cookies' }).click();
  await expect(page.getByLabel('Do not use cookies that measure my website use')).toBeChecked();
  await expect(page.getByLabel('Do not use cookies that help')).toBeChecked();
  await expect(page.getByLabel('Do not use cookies that remember my settings on the site')).toBeChecked();

  await page.getByText('Use cookies that measure my website use', { exact: true }).click();
  await expect(page.getByLabel('Use cookies that measure my website use', { exact: true })).toBeChecked();
  await page.getByRole('button', { name: 'Save changes' }).click();

  // Wait for page to reload
  await expect(page.getByRole('heading', { name: 'Cookies on GOV.UK' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Save changes' })).toBeVisible();

  await assertCookie(page, 'cookies_policy', { usage: true, settings: false, essential: true, campaigns:false });
  await assertCookie(page, 'cookies_preferences_set', 'true');
  await assertCookie(page, 'gov_singleconsent_uid');

  await expect(page.getByLabel('Use cookies that measure my website use', { exact: true })).toBeChecked();
  await expect(page.getByLabel('Do not use cookies that help')).toBeChecked();
  await expect(page.getByLabel('Do not use cookies that remember my settings on the site')).toBeChecked();
  await page.getByRole('link', { name: 'Go back to the page you were' }).click();

  await expect(page.getByLabel('Cookies on GOV.UK')).not.toBeVisible();

  await assertCookie(page, 'cookies_policy', { usage: true, settings: false, essential: true, campaigns:false });
  await assertCookie(page, 'cookies_preferences_set', 'true');
  await assertCookie(page, 'gov_singleconsent_uid');
});
