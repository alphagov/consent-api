const {
  addUrlParameter,
  removeUrlParameter,
  parseUrl,
  buildUrl,
  findByKey,
  isCrossOrigin,
  origin,
} = require('./singleconsent')

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
      jsdom.reconfigure({ url: location });
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
