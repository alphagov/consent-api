const xhrMock = require('xhr-mock').default
const {
  GovSingleConsent,
  addUrlParameter,
  removeUrlParameter,
  parseUrl,
  buildUrl,
  findByKey,
  isCrossOrigin,
  origin,
} = require('./singleconsent')

MOCK_API_URL = 'https://test-url.com/api/'
MOCK_COOKIE_NAME = 'gov_singleconsent_uid'
MOCK_UID = 'test-uid'

let originalCookie

jest.useFakeTimers()

const mockCookie = (name = MOCK_COOKIE_NAME, value = MOCK_UID, days = 1) => {
  const date = new Date()
  date.setTime(date.getTime() + days * 24 * 60 * 60 * 1000)
  const expires = `; expires=${date.toGMTString()}`

  Object.defineProperty(document, 'cookie', {
    writable: true,
    value: `${name}=${value}${expires}; path=/`,
  })
}

const resetCookie = (_document) => {
  if (originalCookie) {
    Object.defineProperty(_document, 'cookie', originalCookie)
  } else {
    delete _document.cookie
  }
}

describe('Consent Management', () => {
  beforeAll(() => {
    originalCookie = Object.getOwnPropertyDescriptor(document, 'cookie')
  })
  beforeEach(() => {
    xhrMock.setup()
    document.body.innerHTML = `<div data-gov-singleconsent-api-url="${MOCK_API_URL}"></div>`
  })

  afterEach(() => {
    xhrMock.teardown()
    resetCookie(document)
  })

  it('should initialise Consent UID to undefined if no initial UID', () => {
    const consentInstance = new GovSingleConsent()
    consentInstance.init(jest.fn(), jest.fn())
    expect(consentInstance.uid).toBeUndefined()
  })

  it('should initialise Consent UID to cookie value if defined', () => {
    mockCookie()
    const response1 = ['a', 'b']
    const response2 = { data: 'ok' }
    xhrMock.get(MOCK_API_URL, (req, res) =>
      res.status(200).body(JSON.stringify(response1))
    )
    xhrMock.get(`${MOCK_API_URL}${MOCK_UID}`, (req, res) =>
      res.status(200).body(JSON.stringify(response2))
    )
    const consentInstance = new GovSingleConsent()
    consentInstance.init(jest.fn(), jest.fn())
    expect(consentInstance.uid).toBe(MOCK_UID)
  })

  it('should timeout the consents if the request takes more than one second', () => {
    mockCookie()
    const response1 = ['a', 'b']
    xhrMock.get(MOCK_API_URL, (req, res) =>
      res.status(200).body(JSON.stringify(response1))
    )
    xhrMock.get(`${MOCK_API_URL}${MOCK_UID}`, (req, res) => {
      return new Promise(() => {})
    })
    const consentInstance = new GovSingleConsent()
    let err
    try {
      consentInstance.init(jest.fn(), jest.fn())
      jest.advanceTimersByTime(1001)
    } catch (e) {
      err = e
    }
    console.log(err)
    expect(err.message).toMatch(/timed out/)
  })

  it('should not timeout the consents if the request takes less than one second', () => {
    mockCookie()
    const response1 = ['a', 'b']
    xhrMock.get(MOCK_API_URL, (req, res) =>
      res.status(200).body(JSON.stringify(response1))
    )
    xhrMock.get(`${MOCK_API_URL}${MOCK_UID}`, (req, res) => {
      return new Promise(() => {})
    })
    const consentInstance = new GovSingleConsent()
    consentInstance.init(jest.fn(), jest.fn())
    jest.advanceTimersByTime(500)
    expect(consentInstance.uid).toBe(MOCK_UID)
  })
})

/*
 *
 *  Utils
 *
 */

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
      jsdom.reconfigure({ url: location })
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
      expect(origin(link)).toEqual(expected)
    })
  })
})
