const DEFAULT_TIMEOUT = 10000

export function request(url, options, onSuccess, onError) {
  try {
    var req = new XMLHttpRequest()
    var isTimeout = false
    options = options || {}

    req.onreadystatechange = function () {
      if (req.readyState === req.DONE) {
        if (req.status >= 200 && req.status < 400) {
          let jsonResponse;
          try {
            jsonResponse = JSON.parse(req.responseText)
          } catch (error) {
            return onError(error)
          }
          onSuccess(JSON.parse(req.responseText))
        } else if (req.status === 0 && req.timeout > 0) {
          // Possible timeout, waiting for ontimeout event
          // Timeout will throw a status = 0 request
          // onreadystatechange preempts ontimeout
          // And we can't know for sure at this stage if it's a timeout
          setTimeout(function () {
            if (isTimeout) {
              return
            }
            return onError(
              new Error(
                'Request to ' + url + ' failed with status: ' + req.status
              )
            )
          }, 500)
        } else {
          return onError(
            new Error('Request to ' + url + ' failed with status: ' + req.status)
          )
        }
      }
    }

    req.open(options.method || 'GET', url, true)

    if (options.timeout) {
      req.timeout = options.timeout
    } else {
      req.timeout = DEFAULT_TIMEOUT
    }

    req.ontimeout = function () {
      isTimeout = true
      return onError(new Error('Request to ' + url + ' timed out'))
    }


    var headers = options.headers || {}
    for (var name in headers) {
      req.setRequestHeader(name, headers[name])
    }

    req.send(options.body || null)
  } catch (error) {
    return onError(error)
  }
}

export function addUrlParameter(url, name, value) {
  url = parseUrl(url)
  var newParam = name.concat('=', value)
  var modified = false
  findByKey(name, url.params, function (index) {
    url.params[index] = newParam
    modified = true
  })
  if (!modified) {
    url.params.push(newParam)
  }
  return buildUrl(url)
}

export function removeUrlParameter(url, name) {
  url = parseUrl(url)
  findByKey(name, url.params, function (index) {
    url.params.splice(index--, 1)
  })
  return buildUrl(url)
}

export function parseUrl(url) {
  var parts = url.split('?')
  return {
    address: parts[0],
    params: (parts[1] || '').split('&').filter(Boolean),
  }
}

export function buildUrl(parts) {
  return [parts.address, parts.params.join('&')].join('?').replace(/\??$/, '')
}

export function findByKey(key: string, keyvals: string[], callback?: Function) {
  key += '='
  for (var index = 0; keyvals.length > index; index++) {
    if (keyvals[index].trim().slice(0, key.length) === key) {
      var value = keyvals[index].trim().slice(key.length)
      if (callback) {
        callback(index, value)
      } else {
        return value
      }
    }
  }
}

export function isCrossOrigin(link) {
  return (
    link.protocol !== window.location.protocol ||
    link.hostname !== window.location.hostname ||
    (link.port || '80') !== (window.location.port || '80')
  )
}

export function getOriginFromLink(link) {
  var origin = link.protocol.concat('//', link.hostname)
  if (link.port && link.port !== '80' && link.port !== '443') {
    origin = origin.concat(':', link.port)
  }
  return origin
}

export function isBrowser() {
  return typeof module === 'undefined'
}

type setCookieParams = {
  name: string
  value: string
  lifetime: number
}
export function setCookie({ name, value, lifetime }: setCookieParams) {
  // const encodedValue = encodeURIComponent(value)
  const encodedValue = value
  document.cookie = name
    .concat('=', encodedValue)
    .concat(
      '; path=/',
      '; max-age='.concat(lifetime.toString()),
      document.location.protocol === 'https:' ? '; Secure' : ''
    )
}

export function getCookie(name: string, defaultValue?: string) {
  name += '='
  const cookies = document.cookie.split(';')
  let cookie = null

  for (let i = 0; i < cookies.length; i++) {
    let currentCookie = cookies[i].trim()
    if (currentCookie.indexOf(name) === 0) {
      cookie = currentCookie
      break
    }
  }

  if (cookie) {
    return decodeURIComponent(cookie.trim().slice(name.length))
  }

  return defaultValue || null
}

export function validateConsentObject(response) {
  try {
    if (typeof response !== 'object' || response === null) {
      return false;
    }

    var expectedKeys = ['essential', 'settings', 'usage', 'campaigns'];
    var allKeysPresent = true;
    var responseKeysCount = 0;

    for (var i = 0; i < expectedKeys.length; i++) {
      if (!(expectedKeys[i] in response)) {
        allKeysPresent = false;
        break;
      }
    }

    var allValuesBoolean = true;
    for (var key in response) {
      if (response.hasOwnProperty(key)) {
        responseKeysCount++;
        if (typeof response[key] !== 'boolean') {
          allValuesBoolean = false;
          break;
        }
      }
    }

    var correctNumberOfKeys = responseKeysCount === expectedKeys.length;

  } catch (err) {
    return false;
  }

  return allKeysPresent && allValuesBoolean && correctNumberOfKeys;
}
