// @ts-ignore
import xhrMock from 'xhr-mock'
import { GovSingleConsent } from './GovSingleConsent'
import { GovConsentConfig } from './GovConsentConfig'

import {
  addUrlParameter,
  removeUrlParameter,
  parseUrl,
  buildUrl,
  findByKey,
  isCrossOrigin,
  getOriginFromLink,
  getCookie,
  validateConsentObject,
} from './utils'

const MOCK_API_BASE_URL = 'https://test-url.com'
const MOCK_COOKIE_NAME = 'gov_singleconsent_uid'
const MOCK_UID = 'test-uid'
const MOCK_URL = 'test-url.com'

const originalLocation = window.location

let originalCookie

// jest.useFakeTimers()

const waitFor = (time) => new Promise((resolve) => setTimeout(resolve, time))

const waitForPromises = () => waitFor(0)

const mockCookie = (name = MOCK_COOKIE_NAME, value = MOCK_UID): void => {
  // A simple cookie logic for testing
  // No timeout, no expiration, no path, no domain
  Object.defineProperty(document, 'cookie', {
    writable: true,
    value: `${document.cookie}${name}=${value};`,
  })
}

const resetCookie = (_document): void => {
  if (originalCookie) {
    Object.defineProperty(_document, 'cookie', originalCookie)
  } else {
    _document.cookie = ''
  }
}

const mockWindowURL = (url?: string): void => {
  Object.defineProperty(window, 'location', {
    writable: true,
    value: { href: url || MOCK_URL },
  })
}

const resetWindowURL = (): void => {
  Object.defineProperty(window, 'location', {
    writable: true,
    value: originalLocation,
  })
}

describe('Consent Management', () => {
  beforeAll(() => {
    originalCookie = Object.getOwnPropertyDescriptor(document, 'cookie')
  })
  beforeEach(() => {
    jest.useRealTimers()
    xhrMock.setup()
    document.body.innerHTML = `<div data-gov-singleconsent-api-url="${MOCK_API_BASE_URL}"></div>`
  })

  afterEach(() => {
    jest.clearAllTimers()
    xhrMock.teardown()
    resetCookie(document)
    resetWindowURL()
  })

  it('should initialise Consent UID to undefined if no initial UID', () => {
    const consentInstance = new GovSingleConsent(jest.fn(), MOCK_API_BASE_URL)
    expect(consentInstance.uid).toBeUndefined()
    expect(getCookie(GovConsentConfig.UID_KEY)).toBe(null)
  })

  it('should initialise Consent UID to cookie value if defined and URL value is not defined', () => {
    mockCookie()
    const response1 = ['a', 'b']
    const response2 = { data: 'ok' }
    xhrMock.get(`${MOCK_API_BASE_URL}/api/v1/origins`, (req, res) =>
      res.status(200).body(JSON.stringify(response1))
    )
    xhrMock.get(`${MOCK_API_BASE_URL}/api/v1/consent/${MOCK_UID}`, (req, res) =>
      res.status(200).body(JSON.stringify(response2))
    )
    const consentInstance = new GovSingleConsent(jest.fn(), MOCK_API_BASE_URL)
    expect(consentInstance.uid).toBe(MOCK_UID)
    expect(getCookie(GovConsentConfig.UID_KEY)).toBe(MOCK_UID)
  })

  it('should initialise Consent UID to URL value if defined and cookie value is not defined', () => {
    const response1 = ['a', 'b']
    const response2 = { data: 'ok' }
    const mockedUrlUid = `test-url-uid`
    const mockedUrl = `${MOCK_URL}?${MOCK_COOKIE_NAME}=${mockedUrlUid}`
    xhrMock.get(`${MOCK_API_BASE_URL}/api/v1/origins`, (req, res) =>
      res.status(200).body(JSON.stringify(response1))
    )
    xhrMock.get(
      `${MOCK_API_BASE_URL}/api/v1/consent/${mockedUrlUid}`,
      (req, res) => res.status(200).body(JSON.stringify(response2))
    )
    mockWindowURL(mockedUrl)
    const consentInstance = new GovSingleConsent(jest.fn(), MOCK_API_BASE_URL)
    expect(consentInstance.uid).toBe(mockedUrlUid)
    expect(getCookie(GovConsentConfig.UID_KEY)).toBe(mockedUrlUid)
  })

  it('should initialise Consent UID to URL value if both URL and cookie values are defined', () => {
    mockCookie()
    const response1 = ['a', 'b']
    const response2 = { data: 'ok' }
    const mockedUrlUid = `test-url-uid`
    const mockedUrl = `${MOCK_URL}?${MOCK_COOKIE_NAME}=${mockedUrlUid}`
    xhrMock.get(`${MOCK_API_BASE_URL}/api/v1/origins`, (req, res) =>
      res.status(200).body(JSON.stringify(response1))
    )
    xhrMock.get(
      `${MOCK_API_BASE_URL}/api/v1/consent/${mockedUrlUid}`,
      (req, res) => res.status(200).body(JSON.stringify(response2))
    )
    mockWindowURL(mockedUrl)
    const consentInstance = new GovSingleConsent(jest.fn(), MOCK_API_BASE_URL)
    expect(consentInstance.uid).toBe(mockedUrlUid)
    expect(getCookie(GovConsentConfig.UID_KEY)).toBe(mockedUrlUid)
  })

  describe('fetching consents', () => {
    describe('Happy path', () => {
      it('should set the consents to whatever the server returns when fetching [case 1]', async () => {
        mockCookie()
        const response1 = ['a', 'b']
        xhrMock.get(`${MOCK_API_BASE_URL}/api/v1/origins`, (req, res) =>
          res.status(200).body(JSON.stringify(response1))
        )
        xhrMock.get(
          `${MOCK_API_BASE_URL}/api/v1/consent/${MOCK_UID}`,
          (req, res) =>
            res.status(200).body(
              JSON.stringify({
                status: GovSingleConsent.ACCEPT_ALL,
              })
            )
        )
        const mockCallback = jest.fn()
        new GovSingleConsent(mockCallback, MOCK_API_BASE_URL)
        await waitForPromises()
        expect(mockCallback).toHaveBeenCalledWith(
          GovSingleConsent.ACCEPT_ALL,
          true,
          null
        )
      })

      it('should set the consents to whatever the server returns when fetching [case 2]', async () => {
        mockCookie()
        const response1 = ['a', 'b']
        xhrMock.get(`${MOCK_API_BASE_URL}/api/v1/origins`, (req, res) =>
          res.status(200).body(JSON.stringify(response1))
        )
        xhrMock.get(
          `${MOCK_API_BASE_URL}/api/v1/consent/${MOCK_UID}`,
          (req, res) =>
            res.status(200).body(
              JSON.stringify({
                status: {
                  campaigns: false,
                  essential: true,
                  settings: false,
                  usage: true,
                },
              })
            )
        )
        const mockCallback = jest.fn()
        new GovSingleConsent(mockCallback, MOCK_API_BASE_URL)
        await waitForPromises()
        expect(mockCallback).toHaveBeenCalledWith(
          { campaigns: false, essential: true, settings: false, usage: true },
          true,
          null
        )
      })
    })
    describe('Unhappy paths', () => {
      it('should reject the consents if fetchconsents response format is bad JSON', async () => {
        mockCookie()
        const response1 = ['a', 'b']
        xhrMock.get(`${MOCK_API_BASE_URL}/api/v1/origins`, (req, res) =>
          res.status(200).body(JSON.stringify(response1))
        )
        xhrMock.get(
          `${MOCK_API_BASE_URL}/api/v1/consent/${MOCK_UID}`,
          (req, res) => res.status(200).body('bad response')
        )
        const mockCallback = jest.fn()
        new GovSingleConsent(mockCallback, MOCK_API_BASE_URL)
        await waitForPromises()
        expect(mockCallback).toHaveBeenCalledWith(
          GovSingleConsent.REJECT_ALL,
          true,
          expect.any(Error)
        )
        expect(mockCallback.mock.calls[0][2].message).toMatch(
          /Unexpected token b in JSON/
        )
      })

      it('should reject the consents if fetchconsents response format is bad object shape', async () => {
        mockCookie()
        const response1 = ['a', 'b']
        xhrMock.get(`${MOCK_API_BASE_URL}/api/v1/origins`, (req, res) =>
          res.status(200).body(JSON.stringify(response1))
        )
        xhrMock.get(
          `${MOCK_API_BASE_URL}/api/v1/consent/${MOCK_UID}`,
          (req, res) =>
            res.status(200).body(JSON.stringify({ someKey: 'someValue' }))
        )
        const mockCallback = jest.fn()
        new GovSingleConsent(mockCallback, MOCK_API_BASE_URL)
        await waitForPromises()
        expect(mockCallback).toHaveBeenCalledWith(
          GovSingleConsent.REJECT_ALL,
          true,
          expect.any(Error)
        )
        expect(mockCallback.mock.calls[0][2].message).toMatch(
          /Invalid consents object returned from the API/
        )
      })

      it('should reject the consents if fetchconsents request fails', async () => {
        mockCookie()
        const response1 = ['a', 'b']
        xhrMock.get(`${MOCK_API_BASE_URL}/api/v1/origins`, (req, res) =>
          res.status(200).body(JSON.stringify(response1))
        )
        xhrMock.get(
          `${MOCK_API_BASE_URL}/api/v1/consent/${MOCK_UID}`,
          (req, res) => res.status(500).body('Some error')
        )
        const mockCallback = jest.fn()
        new GovSingleConsent(mockCallback, MOCK_API_BASE_URL)
        await waitForPromises()
        expect(mockCallback).toHaveBeenCalledWith(
          GovSingleConsent.REJECT_ALL,
          true,
          expect.any(Error)
        )
        expect(mockCallback.mock.calls[0][2].message).toMatch(
          /Request to https:[\/\.\w\s-]+failed with status: 500/
        )
      })

      it('should reject the consents if fetchconsents times out', () => {
        jest.useFakeTimers()
        mockCookie()
        const response1 = ['a', 'b']
        xhrMock.get(`${MOCK_API_BASE_URL}/api/v1/origins`, (req, res) =>
          res.status(200).body(JSON.stringify(response1))
        )
        xhrMock.get(
          `${MOCK_API_BASE_URL}/api/v1/consent/${MOCK_UID}`,
          (req, res) => {
            return new Promise(() => {})
          }
        )
        let err
        const mockCallback = jest.fn()

        new GovSingleConsent(mockCallback, MOCK_API_BASE_URL)
        jest.advanceTimersByTime(1001)
        expect(mockCallback).toHaveBeenCalledWith(
          GovSingleConsent.REJECT_ALL,
          true,
          expect.any(Error)
        )
        expect(mockCallback.mock.calls[0][2].message).toMatch(/timed out/)
      })
    })
  })

  describe('setting consents', () => {
    describe('Happy path', () => {
      it('should set the consents and the UID the first time the request succeeds', async () => {
        const response1 = ['a', 'b']
        xhrMock.get(`${MOCK_API_BASE_URL}/api/v1/origins`, (req, res) =>
          res.status(200).body(JSON.stringify(response1))
        )
        xhrMock.get(
          `${MOCK_API_BASE_URL}/api/v1/consent/${MOCK_UID}`,
          (req, res) =>
            res.status(200).body(
              JSON.stringify({
                status: GovSingleConsent.ACCEPT_ALL,
              })
            )
        )

        xhrMock.post(`${MOCK_API_BASE_URL}/api/v1/consent`, (req, res) =>
          res.status(200).body(
            JSON.stringify({
              uid: MOCK_UID,
            })
          )
        )
        const mockCallback = jest.fn()
        const sconManager = new GovSingleConsent(
          mockCallback,
          MOCK_API_BASE_URL
        )
        await waitForPromises()
        // Since no UID was passed in URL nor cookie, no consent should be set
        expect(mockCallback).toHaveBeenCalledWith(null, false, null)

        // Simulate what would happen if the user accepts all consents by clicking on a cookie banner
        sconManager.setConsents(GovSingleConsent.ACCEPT_ALL)

        await waitForPromises()

        expect(mockCallback).toHaveBeenCalledWith(
          GovSingleConsent.ACCEPT_ALL,
          true,
          null
        )
      })

      it('should update the consents when the request succeeds', async () => {
        mockCookie()
        const response1 = ['a', 'b']
        xhrMock.get(`${MOCK_API_BASE_URL}/api/v1/origins`, (req, res) =>
          res.status(200).body(JSON.stringify(response1))
        )
        xhrMock.get(
          `${MOCK_API_BASE_URL}/api/v1/consent/${MOCK_UID}`,
          (req, res) =>
            res.status(200).body(
              JSON.stringify({
                status: GovSingleConsent.ACCEPT_ALL,
              })
            )
        )
        xhrMock.post(`${MOCK_API_BASE_URL}/api/v1/consent/${MOCK_UID}`, (req, res) =>
          res.status(200).body(
            JSON.stringify({
              uid: MOCK_UID,
            })
          )
        )

        const mockCallback = jest.fn()
        const sconManager = new GovSingleConsent(
          mockCallback,
          MOCK_API_BASE_URL
        )
        await waitForPromises()

        // Simulate what would happen if the user changed their consents on the cookie management page and opted out of campaigns
        const newConsents = { ...GovSingleConsent.ACCEPT_ALL, campaigns: false }
        sconManager.setConsents(newConsents)

        await waitForPromises()

        expect(mockCallback).toHaveBeenCalledWith(newConsents, true, null)
      })
    })

    describe('Unhappy paths', () => {
      it('should set the consents to rejected if the update consents request returns bad JSON', async () => {
        const response1 = ['a', 'b']
        xhrMock.get(`${MOCK_API_BASE_URL}/api/v1/origins`, (req, res) =>
          res.status(200).body(JSON.stringify(response1))
        )
        xhrMock.get(
          `${MOCK_API_BASE_URL}/api/v1/consent/${MOCK_UID}`,
          (req, res) =>
            res.status(200).body(
              JSON.stringify({
                status: GovSingleConsent.ACCEPT_ALL,
              })
            )
        )

        xhrMock.post(`${MOCK_API_BASE_URL}/api/v1/consent`, (req, res) =>
          res.status(200).body('bad json')
        )
        const mockCallback = jest.fn()
        const sconManager = new GovSingleConsent(
          mockCallback,
          MOCK_API_BASE_URL
        )
        await waitForPromises()

        // Simulate what would happen if the user accepts all consents by clicking on a cookie banner
        sconManager.setConsents(GovSingleConsent.ACCEPT_ALL)

        await waitForPromises()

        expect(mockCallback).toHaveBeenCalledWith(
          GovSingleConsent.REJECT_ALL,
          true,
          expect.any(Error)
        )
        expect(mockCallback.mock.calls[1][2].message).toMatch(
          /Unexpected token b in JSON/
        )
      })

      it('should set the consents to rejected if the update consents request returns bad object shape', async () => {
        const response1 = ['a', 'b']
        xhrMock.get(`${MOCK_API_BASE_URL}/api/v1/origins`, (req, res) =>
          res.status(200).body(JSON.stringify(response1))
        )
        xhrMock.get(
          `${MOCK_API_BASE_URL}/api/v1/consent/${MOCK_UID}`,
          (req, res) =>
            res.status(200).body(
              JSON.stringify({
                status: GovSingleConsent.ACCEPT_ALL,
              })
            )
        )

        xhrMock.post(`${MOCK_API_BASE_URL}/api/v1/consent`, (req, res) =>
          res.status(200).body(JSON.stringify({ badKey: 'bad value' }))
        )
        const mockCallback = jest.fn()
        const sconManager = new GovSingleConsent(
          mockCallback,
          MOCK_API_BASE_URL
        )
        await waitForPromises()

        // Simulate what would happen if the user accepts all consents by clicking on a cookie banner
        sconManager.setConsents(GovSingleConsent.ACCEPT_ALL)

        await waitForPromises()

        expect(mockCallback).toHaveBeenCalledWith(
          GovSingleConsent.REJECT_ALL,
          true,
          expect.any(Error)
        )
        expect(mockCallback.mock.calls[1][2].message).toMatch(
          /No UID returned from the API/
        )
      })

      it('should set the consents to rejected if the update consents request fails', async () => {
        const response1 = ['a', 'b']
        xhrMock.get(`${MOCK_API_BASE_URL}/api/v1/origins`, (req, res) =>
          res.status(200).body(JSON.stringify(response1))
        )
        xhrMock.get(
          `${MOCK_API_BASE_URL}/api/v1/consent/${MOCK_UID}`,
          (req, res) =>
            res.status(200).body(
              JSON.stringify({
                status: GovSingleConsent.ACCEPT_ALL,
              })
            )
        )

        xhrMock.post(`${MOCK_API_BASE_URL}/api/v1/consent`, (req, res) =>
          res.status(500).body("Some error")
        )
        const mockCallback = jest.fn()
        const sconManager = new GovSingleConsent(
          mockCallback,
          MOCK_API_BASE_URL
        )
        await waitForPromises()

        // Simulate what would happen if the user accepts all consents by clicking on a cookie banner
        sconManager.setConsents(GovSingleConsent.ACCEPT_ALL)

        await waitForPromises()

        expect(mockCallback).toHaveBeenCalledWith(
          GovSingleConsent.REJECT_ALL,
          true,
          expect.any(Error)
        )
        expect(mockCallback.mock.calls[1][2].message).toMatch(
          /Request to https:[\/\.\w\s-]+failed with status: 500/
        )
      })

    })
  })

  describe('[method]: isConsentPreferencesSet', () => {
    it('should return false if the cookie is not set', () => {
      new GovSingleConsent(jest.fn(), `${MOCK_API_BASE_URL}/api/v1/consent`)
      expect(GovSingleConsent.isConsentPreferencesSet()).toBe(false)
    })

    it('should return true if the cookie is set', () => {
      new GovSingleConsent(jest.fn(), `${MOCK_API_BASE_URL}/api/v1/consent`)
      mockCookie(GovConsentConfig.PREFERENCES_SET_COOKIE_NAME, 'true')
      expect(GovSingleConsent.isConsentPreferencesSet()).toBe(true)
    })
  })
})

/*
 *
 *  Utils
 *
 */
describe("[Unit tests]: utils", () => {
  describe('addUrlParameter', () => {
    ;[
      {
        url: 'https://example.com',
        name: 'foo',
        value: '1',
        expected: 'https://example.com?foo=1',
      },
      {
        url: 'https://example.com?foo=1',
        name: 'foo',
        value: '1',
        expected: 'https://example.com?foo=1',
      },
      {
        url: 'https://example.com?foo=1',
        name: 'foo',
        value: '2',
        expected: 'https://example.com?foo=2',
      },
      {
        url: 'https://example.com?foo=1',
        name: 'bar',
        value: '2',
        expected: 'https://example.com?foo=1&bar=2',
      },
    ].forEach(({ url, name, value, expected }) => {
      test(`returns ${expected} when the param name to add is ${name}, the value is ${value} and the url is ${url}`, () => {
        expect(addUrlParameter(url, name, value)).toEqual(expected)
      })
    })
  })

  describe('removeUrlParameter', () => {
    ;[
      {
        url: 'https://example.com?foo=1',
        name: 'foo',
        expected: 'https://example.com',
      },
      {
        url: 'https://example.com?foo=1',
        name: 'bar',
        expected: 'https://example.com?foo=1',
      },
      {
        url: 'https://example.com?a=1&b=2',
        name: 'a',
        expected: 'https://example.com?b=2',
      },
      {
        url: 'https://example.com?a=1&b=2',
        name: 'b',
        expected: 'https://example.com?a=1',
      },
      {
        url: 'https://example.com?a=1&b=2&c=3',
        name: 'b',
        expected: 'https://example.com?a=1&c=3',
      },
    ].forEach(({ url, name, expected }) => {
      test(`returns ${expected} when the param name to remove is ${name} and the url is ${url}`, () => {
        expect(removeUrlParameter(url, name)).toEqual(expected)
      })
    })
  })

  describe('getCookie', () => {
    const testSettings: {
      mockCookies: any[]
      cookieName: string
      expected: string
      defaultValue?: string
    }[] = [
      // get cookie when it exists
      {
        mockCookies: [{ name: 'foo', value: '1' }],
        cookieName: 'foo',
        expected: '1',
      },
      // get cookie when it exists amongst other cookies
      {
        mockCookies: [
          { name: 'foo1', value: '1' },
          { name: 'foo2', value: '2' },
          { name: 'foo3', value: '3' },
        ],
        cookieName: 'foo2',
        expected: '2',
      },
      // get cookie when it doesn't exist and no default value specified
      {
        mockCookies: [{ name: 'foo', value: '1' }],
        cookieName: 'none',
        expected: null,
      },
      // get cookie when it doesn't exist and default value specified
      {
        mockCookies: [{ name: 'foo', value: '1' }],
        cookieName: 'none',
        defaultValue: '123',
        expected: '123',
      },
    ]

    testSettings.forEach(
      ({ mockCookies, cookieName, expected, defaultValue }) => {
        test(`returns ${expected} when the cookie is amongst ${mockCookies.length} cookies and the name is ${cookieName} and the default value is ${defaultValue}`, () => {
          mockCookies.forEach((cookie) => {
            const { name, value } = cookie
            mockCookie(name, value)
          })
          expect(getCookie(cookieName, defaultValue)).toEqual(expected)
        })
      }
    )
  })

  describe('parseUrl', () => {
    ;[
      {
        url: 'https://example.com',
        expected: { address: 'https://example.com', params: [] },
      },
      {
        url: 'https://example.com?foo=1',
        expected: { address: 'https://example.com', params: ['foo=1'] },
      },
      {
        url: 'https://example.com?a=1&b=2',
        expected: { address: 'https://example.com', params: ['a=1', 'b=2'] },
      },
    ].forEach(({ url, expected }) => {
      test(`returns an object with an address attribute ${expected.address} and params attribute ${expected.params} when the given url is ${url}`, () => {
        const result = parseUrl(url)
        expect(result.address).toEqual(expected.address)
        expect(result.params).toEqual(expected.params)
      })
    })
  })

  describe('buildUrl', () => {
    ;[
      { parts: { address: 'example.com', params: [] }, expected: 'example.com' },
      {
        parts: { address: 'example.com', params: ['foo=1'] },
        expected: 'example.com?foo=1',
      },
      {
        parts: { address: 'example.com', params: ['foo=1', 'bar=2'] },
        expected: 'example.com?foo=1&bar=2',
      },
    ].forEach(({ parts, expected }) => {
      test(`returns ${expected} if the argument address is ${parts.address} and the argument params are ${parts.params}`, () => {
        expect(buildUrl(parts)).toEqual(expected)
      })
    })
  })

  describe('findByKey', () => {
    ;[
      { kvPairs: ['foo=1', 'bar=2'], key: 'foo', expected: '1' },
      { kvPairs: ['foo=1', 'bar=2'], key: 'bar', expected: '2' },
      { kvPairs: ['foo=1', 'bar=2'], key: 'baz', expected: undefined },
    ].forEach(({ kvPairs, key, expected }) => {
      test(`returns ${expected} if the key is ${key} and the kvPairs are ${kvPairs}`, () => {
        expect(findByKey(key, kvPairs)).toEqual(expected)
      })
    })
    ;[
      {
        kvPairs: ['foo=1', 'bar=2'],
        key: 'foo',
        expectedIndex: 0,
        expectedValue: '1',
      },
      {
        kvPairs: ['foo=1', 'bar=2'],
        key: 'bar',
        expectedIndex: 1,
        expectedValue: '2',
      },
    ].forEach(({ kvPairs, key, expectedIndex, expectedValue }) => {
      test(`calls the given callback with the found index ${expectedIndex} and value ${expectedValue} as arguments if the key is ${key} and the kvPairs are ${kvPairs}`, () => {
        const callback = jest.fn()
        findByKey('foo', ['foo=1', 'bar=2'], callback)
        expect(callback.mock.lastCall).toEqual([0, '1'])
      })
    })
  })

  describe('isCrossOrigin', () => {
    ;[
      {
        url: 'https://example.com',
        location: 'https://example.com',
        expected: false,
      },
      {
        url: 'https://example.com:80',
        location: 'https://example.com',
        expected: false,
      },
      {
        url: 'https://example.com',
        location: 'https://example.com:80',
        expected: false,
      },
      {
        url: 'https://example.com:80',
        location: 'https://example.com:80',
        expected: false,
      },
      {
        url: 'http://example.com:80',
        location: 'https://example.com',
        expected: true,
      },
      {
        url: 'https://example2.com:80',
        location: 'https://example.com',
        expected: true,
      },
      {
        url: 'https://example.com:8080',
        location: 'https://example.com',
        expected: true,
      },
    ].forEach(({ url, location, expected }) => {
      test(`returns ${expected} when passed ${url} and the current URL is ${location}`, () => {
        global.jsdom.reconfigure({ url: location })
        var link = document.createElement('a')
        link.href = url
        expect(isCrossOrigin(link)).toBe(expected)
      })
    })
  })

  describe('origin', function () {
    ;[
      { url: 'http://www.example.com:80', expected: 'http://www.example.com' },
      {
        url: 'http://www.example.com:8080',
        expected: 'http://www.example.com:8080',
      },
      { url: 'http://www.example.com/foo', expected: 'http://www.example.com' },
    ].forEach(({ url, expected }) => {
      test(`returns the origin of a link href url: ${url}`, function () {
        var link = document.createElement('a')
        link.href = url
        expect(getOriginFromLink(link)).toEqual(expected)
      })
    })
  })

  describe('validateConsentObject', () => {
    it('should return false if the object is undefined', () => {
      const response = undefined
      expect(validateConsentObject(response)).toBe(false)
    })
    it('should return false if the object is null', () => {
      const response = null
      expect(validateConsentObject(response)).toBe(false)
    })
    it('should return true if the object is valid', () => {
      const response = GovSingleConsent.REJECT_ALL
      expect(validateConsentObject(response)).toBe(true)
    })
    it('should return false if the object is not an object', () => {
      const response = 'not an object'
      expect(validateConsentObject(response)).toBe(false)
    })
    it('should return false if the object is missing keys', () => {
      const response = { essential: true, usage: false, campaigns: false }
      expect(validateConsentObject(response)).toBe(false)
    })
    it('should return false if the object has extra keys', () => {
      const response = {
        essential: true,
        settings: false,
        usage: false,
        campaigns: false,
        extra: true,
      }
      expect(validateConsentObject(response)).toBe(false)
    })
  })
})
