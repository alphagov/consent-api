# Single Consent client

The Single Consent client is a small Javascript which can be embedded in a
website to enable easily sharing a user's consent or rejection of cookies across
different websites.

See the [Single Consent service README](../README.md).

## Quick start

### 1. Install

In order to set first-party cookies, the client Javascript must be served with
your application.

#### Option A. Install with npm (recommended)

We recommend installing the Single Consent client using
[node package manager (npm)](https://www.npmjs.com/).

Add the following to your `package.json` file in the `dependencies` section:

```json
"@alphagov/consent-api": "alphagov/consent-api#semver:^1.7",
```

#### Option B. Install by using downloaded file

Alternatively, you can download the client from Github. You will need to check
for updates manually.

### 2. Including the Javascript client

The client needs to be loaded on any page that could be an entry point to your
web application, that allows modifying cookie consent, or provides a link to
another domain with which you want to share cookie consent status. It is
probably easiest to add the script to a base template used for all pages.

It is common practice to add Javascript tags just before the end `</body>` tag,
eg:

```html
    ...

    <script src="{path_to_client_js}/singleconsent.js"></script>
  </body>
</html>
```

### 3. Register a callback

The client will automatically check for a unique ID in a cookie or URL parameter
on page load. If it finds one, it will query the Single Consent API and call any
registered callback functions with the returned consent data.

To trigger your Javascript code to (for example) hide your cookie banner if the
user has shared consent, you need to register a callback function with the
following example Javascript code:

```javascript
GovSingleConsent.onStatusLoaded(function (consentData) {
  document.querySelector('#example-cookie-banner-id').hidden = true
})
```

### 4. Share the user's consent to cookies via the API

When the user interacts with your cookie banner or cookie settings page to
consent to or reject cookies you can update the central database by invoking the
following function:

```javascript
exampleCookieConsentStatusObject = {
  essential: true,
  settings: false,
  usage: true,
  campaigns: false,
}

GovSingleConsent.setStatus(exampleCookieConsentStatusObject)
```

The structure of the consent data object is currently based on the
[GOV.UK `cookies_policy` cookie](https://www.gov.uk/help/cookies). If your
website cookies do not fall into any of the four categories listed, please
contact us.

### 5. Configuration

The client connects to the Single Consent service Production environment by
default.

If you need to direct the client to an alternative URL (for example, during
testing), you can add a `data-gov-singleconsent-api-url` attribute to the `body` tag in
your HTML file, eg:

```html
<body
  data-gov-singleconsent-api-url="https://consent-api-nw.a.run.app/api/v1/consent/"
></body>
```

#### Content Security Policy

If your website is served with a
[`Content-Security-Policy` HTTP header or `<meta>` element](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP), you
may need to modify it to allow the client to access the Single Consent service.
The value of the header or meta element should contain the following:

```
connect-src 'self' https://consent-api-nw.a.run.app/api/v1/consent [... other site URLs separated by spaces];
```

## API

The client Javascript adds a `Consent` object to the `window`, allowing you to
call its methods from your own script.

### Methods

#### onStatusLoaded

Add a callback function to be invoked when the client receives a consent status
from the API. The consent status is automatically requested on page load, and if
the API responds, the callback will be invoked with the consent status object as
an argument.

##### Arguments

<table>
<tr valign="top"><th align="left"><code>callback</code> (required)</th><td align="left">A callback function which will be called
with the consent status object as an argument.</td></tr>
</table>

##### Example

```javascript
GovSingleConsent.onStatusLoaded((status) => {
  console.log('Consent Status:')
  console.log(`- Essential cookies (${status.essential})`)
  console.log(`- Campaign cookies (${status.campaigns})`)
  console.log(`- Settings cookies (${status.settings})`)
  console.log(`- Usage cookies (${status.usage})`)
})
```

#### setStatus

Set the current user's consent status in the API, to be shared with other
domains. The method returns immediately, but is processed asynchronously. When
the API has been successfully updated, the callback method is invoked (if
provided).

##### Arguments

<table>
<tr valign="top"><th align="left"><code>status</code> (required)</th><td align="left">A consent status JSON object. Eg:
<pre>
{
  "essential": true,
  "campaigns": false,
  "settings": false,
  "usage": false
}
</pre>
</td></tr>
<tr valign="top"><th align="left"><code>callback</code></th><td align="left">An
optional callback function which will be called
with the consent status as an argument.</td></tr>
</table>

##### Example

```javascript
GovSingleConsent.setStatus(acceptAllCookies, (status) => {
  console.log('Consent status successfully updated to', status)
})
```

## Getting updates

To be notified when there's a new release, you can watch the
[consent-api Github repository](https://github.com/alphagov/consent-api).
