;(function () {
  'use strict'

  var uidKey = 'single_consent_uid'
  var uidFromCookie = findByKey(uidKey, document.cookie.split(';'))
  var uidFromUrl = findByKey(uidKey, parseUrl(location.href).params)
  var apiUrl = (function ($el) {
    return $el
      ? $el.dataset.singleConsentApiUrl.replace(/\/?$/, '/')
      : 'https://consent-api-bgzqvpmbyq-nw.a.run.app/api/v1/consent/'
  })(document.querySelector('[data-single-consent-api-url]'))
  var originPattern = /^(https?:)?\/\/([^:/]+)(?::(\d+))?/

  function SingleConsent() {
    // one year in milliseconds
    this.COOKIE_LIFETIME = 365 * 24 * 60 * 60 * 1000
    this.eventListeners = []
  }

  SingleConsent.prototype.init = function () {
    // hide uid URL parameter
    history.replaceState(null, null, removeUrlParameter(location.href, uidKey))

    // get the current uid from the cookie or the URL if it exists
    setUid(this, uidFromCookie || uidFromUrl)
    if (this.uid) {
      // fetch consent status from API and notify listeners on response
      request(
        apiUrl.concat(this.uid),
        {},
        function (response) {
          this.eventListeners.forEach(function (callback) {
            callback(response.status)
          })
        }.bind(this)
      )
    }
  }

  SingleConsent.prototype.onStatusLoaded = function (callback) {
    this.eventListeners.push(callback)
  }

  SingleConsent.prototype.setStatus = function (status) {
    if (status) {
      request(
        apiUrl.concat(this.uid || ''),
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: 'status='.concat(JSON.stringify(status)),
        },
        function (response) {
          // get the current uid from the API if we don't already have one
          setUid(this, response.uid)
        }.bind(this)
      )
    }
  }

  function setUid(singleConsent, uid) {
    if (uid && uid !== singleConsent.uid) {
      singleConsent.uid = uid

      // add uid URL parameter to consent sharing links
      var links = document.querySelectorAll('a[href]')
      Array.prototype.forEach.call(links, function (link) {
        if (isCrossOrigin(link.href)) {
          link.addEventListener('click', function (event) {
            event.target.href = addUrlParameter(event.target.href, uidKey, uid)
          })
        }
      })

      // set uid cookie
      document.cookie = uidKey
        .concat('=', uid)
        .concat(
          '; path=/',
          '; max-age='.concat(SingleConsent.COOKIE_LIFETIME),
          document.location.protocol === 'https:' ? '; Secure' : ''
        )
    }
  }

  function request(url, options, callback) {
    var req = new XMLHttpRequest()
    options = options || {}
    req.onreadystatechange = function () {
      if (
        req.readyState === req.DONE &&
        (req.status === 0 || (req.status >= 200 && req.status < 400))
      ) {
        callback(JSON.parse(req.responseText))
      }
    }
    req.open(options.method || 'GET', url)
    for (var name in options.headers || {}) {
      req.setRequestHeader(name, options.headers[name])
    }
    req.send(options.body || null)
  }

  function addUrlParameter(url, name, value) {
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

  function removeUrlParameter(url, name) {
    url = parseUrl(url)
    findByKey(name, url.params, function (index) {
      url.params.splice(index--, 1)
    })
    return buildUrl(url)
  }

  function parseUrl(url) {
    var parts = url.split('?')
    return {
      address: parts[0],
      params: (parts[1] || '').split('&').filter(Boolean),
    }
  }

  function buildUrl(parts) {
    return [parts.address, parts.params.join('&')].join('?').replace(/\??$/, '')
  }

  function findByKey(key, keyvals, callback) {
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

  function isCrossOrigin(url) {
    var match = url.match(originPattern)
    if (match) {
      return (
        (match[1] && match[1] !== window.location.protocol) ||
        (match[2] && match[2] !== window.location.hostname) ||
        (match[3] || '80') !== (window.location.port || '80')
      )
    }
    return false
  }

  document.addEventListener('DOMContentLoaded', function () {
    window.SingleConsent = new SingleConsent()
    window.SingleConsent.init()
  })
})()
