;(function () {
  'use strict'

  var Utils = (window.Utils = {})

  Utils.acceptedAdditionalCookies = function (cookiesPolicy) {
    for (var category in cookiesPolicy) {
      if (
        Object.prototype.hasOwnProperty.call(cookiesPolicy, category) &&
        category !== 'essential' &&
        cookiesPolicy[category]
      ) {
        return true
      }
    }
    return false
  }

  Utils.isEmpty = function (obj) {
    for (var x in obj) {
      if (Object.prototype.hasOwnProperty.call(obj, x)) return false
    }
    return true
  }

  Utils.getCookie = function (name, defaultValue) {
    name += '='
    var cookies = document.cookie.split(';')
    for (var index = 0; cookies.length > index; index++) {
      if (cookies[index].trim().slice(0, name.length) === name) {
        return decodeURIComponent(cookies[index].trim().slice(name.length))
      }
    }
    return defaultValue || null
  }

  Utils.setCookie = function (name, value, options) {
    document.cookie = name
      .concat('=', value)
      .concat(
        '; path=/',
        options.days
          ? '; max-age='.concat(options.days * 24 * 60 * 60 * 1000)
          : '',
        document.location.protocol === 'https:' ? '; Secure' : ''
      )
  }
})()
