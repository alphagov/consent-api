import { expect } from "@playwright/test";

const getCurrentDomain = async (page) => {
  const url = new URL(page.url());
  return url.hostname;
};

export const assertCookie = async (page, name: string, value?, customDomain?) => {
  /*
  * / Asserts the presence and, optionally, the value of a cookie by name and domain on a Playwright page object.
  */
  const domain = customDomain || await getCurrentDomain(page);
  let cookies = await page.context().cookies();
  let cookie = cookies.find((c) => c.name === name && c.domain.includes(domain));
  expect(cookie).toBeDefined();
  if (value) {
    const cookieValue =
      typeof value === "string" ? cookie.value : JSON.parse(cookie.value);
    expect(cookieValue).toEqual(value);
  }
};

export const clearCookies = async (page) => {
  await page.context().clearCookies();
  await expect(page.context().cookies()).resolves.toEqual([]);
};
