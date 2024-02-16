import { expect } from "@playwright/test";

export const assertCookie = async (page, name: string, value?) => {
  let cookies = await page.context().cookies();
  let cookie = cookies.find((c) => c.name === name);
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
