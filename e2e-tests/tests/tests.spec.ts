import { test, expect } from '@playwright/test';
import {assertCookie, clearCookies} from './utils';

const serviceOneOrigin = process.env.DUMMY_SERVICE_1_ORIGIN || 'http://localhost:8001';
const serviceTwoOrigin = process.env.DUMMY_SERVICE_2_ORIGIN || 'http://localhost:8002';


test('I can manage the cookies on a single domain, starting with a rejection', async ({ page }) => {
  // Load service 1 and reject cookies
  await page.goto(`${serviceOneOrigin}/dummy-service/`);
  await clearCookies(page)
  await expect(page.getByLabel('Cookies on GOV.UK')).toBeVisible();
  await page.getByRole('button', { name: 'Reject analytics cookies' }).click();


  await expect(page.getByLabel('Cookies on GOV.UK')).not.toBeVisible();

  await assertCookie(page, 'cookies_policy', { usage: false, settings: false, essential: true, campaigns:false });
  await assertCookie(page, 'cookies_preferences_set', 'true');
  await assertCookie(page, 'gov_singleconsent_uid',);

  // Go to the cookies page and change the consents
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

test('I can manage cookies across domains', async ({ page }) => {
  // Clear cookies on both services
  await page.goto(`${serviceOneOrigin}`);
  await clearCookies(page)
  await page.goto(`${serviceTwoOrigin}`);
  await clearCookies(page)

  // Accept cookies on service 1 and consent to cookies
  await page.goto(`${serviceOneOrigin}/dummy-service`);
  await expect(page.getByLabel('Cookies on GOV.UK')).toBeVisible();
  await page.getByRole('button', { name: 'Accept analytics cookies' }).click();
  await expect(page.getByLabel('Cookies on GOV.UK')).not.toBeVisible();

  await assertCookie(page, 'cookies_policy', { usage: true, settings: true, essential: true, campaigns:true });
  await assertCookie(page, 'cookies_preferences_set', 'true');
  await assertCookie(page, 'gov_singleconsent_uid',);

  // Go to service 2
  await page.getByRole('link', { name: 'Another service' }).click();
  await expect(page.getByRole('link', { name: 'Start now' })).toBeVisible();
  await page.getByRole('link', { name: 'Start now' }).click();

  await expect(page.getByRole('banner')).toBeVisible();
  await expect(page.getByLabel('Cookies on GOV.UK')).not.toBeVisible();

  // Assert consents have been shared across with service 2
  await assertCookie(page, 'cookies_policy', { usage: true, settings: true, essential: true, campaigns:true });
  await assertCookie(page, 'cookies_preferences_set', 'true');
  await assertCookie(page, 'gov_singleconsent_uid',);

  await page.getByRole('link', { name: 'Cookies' }).click();
  await expect(page.getByRole('heading', { name: 'Cookies on GOV.UK' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Save changes' })).toBeVisible();

  await expect(page.getByLabel('Use cookies that measure my website use', { exact: true })).toBeChecked();
  await expect(page.getByLabel('Use cookies that help with communications and marketing', { exact: true })).toBeChecked();
  await expect(page.getByLabel('Use cookies that remember my settings on the site', { exact: true })).toBeChecked();

  // Change consents on service 2
  await page.getByLabel('Do not use cookies that help').click();
  await expect(page.getByLabel('Do not use cookies that help')).toBeChecked();
  await page.getByRole('button', { name: 'Save changes' }).click();


  await expect(page.getByRole('heading', { name: 'Cookies on GOV.UK' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Save changes' })).toBeVisible();
  await expect(page.getByLabel('Do not use cookies that help')).toBeChecked();

  await assertCookie(page, 'cookies_policy', { usage: true, settings: true, essential: true, campaigns:false });
  await assertCookie(page, 'cookies_preferences_set', 'true');
  await assertCookie(page, 'gov_singleconsent_uid',);

  // Go back to service 1
  await page.getByRole('link', { name: 'Go back to the page you were' }).click();
  await page.getByRole('link', { name: 'Another service' }).click();
  await expect(page.getByRole('link', { name: 'Start now' })).toBeVisible();
  await page.getByRole('link', { name: 'Start now' }).click();

  await expect(page.getByRole('banner')).toBeVisible();
  await expect(page.getByLabel('Cookies on GOV.UK')).not.toBeVisible();

  // Consents have been shared across with service 1
  await assertCookie(page, 'cookies_policy', { usage: true, settings: true, essential: true, campaigns:false });
  await assertCookie(page, 'cookies_preferences_set', 'true');
  await assertCookie(page, 'gov_singleconsent_uid',);

  // And the change is also reflected on the cookies page of service 1
  await page.getByRole('link', { name: 'Cookies' }).click();
  await expect(page.getByRole('heading', { name: 'Cookies on GOV.UK' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Save changes' })).toBeVisible();

  await expect(page.getByLabel('Use cookies that measure my website use', { exact: true })).toBeChecked();
  await expect(page.getByLabel('Use cookies that help with communications and marketing', { exact: true })).not.toBeChecked();
  await expect(page.getByLabel('Do not use cookies that help')).toBeChecked();
  await expect(page.getByLabel('Use cookies that remember my settings on the site', { exact: true })).toBeChecked();
});
