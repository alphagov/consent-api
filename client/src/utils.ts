export function request(url, options, onSuccess) {
  var req = new XMLHttpRequest()
  var isTimeout = false
  options = options || {}

  req.onreadystatechange = function () {
    if (req.readyState === req.DONE) {
      if (req.status >= 200 && req.status < 400) {
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
          throw new Error(
            'Request to ' + url + ' failed with status: ' + req.status
          )
        }, 500)
      } else {
        throw new Error(
          'Request to ' + url + ' failed with status: ' + req.status
        )
      }
    }
  }

  if (options.timeout) {
    req.timeout = options.timeout
  }

  req.ontimeout = function () {
    isTimeout = true
    throw new Error('Request to ' + url + ' timed out')
  }

  req.open(options.method || 'GET', url, true)

  var headers = options.headers || {}
  for (var name in headers) {
    req.setRequestHeader(name, headers[name])
  }

  req.send(options.body || null)
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
  if (link.port && link.port !== '80') {
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
