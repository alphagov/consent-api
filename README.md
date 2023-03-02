# Single Consent API

This is a HTTP API and simple frontend app, which holds user consent to cookies in a
central database.

This enables web services to share user consent status across multiple domains.


## Installation

In order to set first-party cookies, the client Javascript must be served with
your application. One way to do this is to install it with `npm`. Add the
following to the `dependencies` section of your `package.json`:

```json
"@alphagov/consent-api": "alphagov/consent-api#semver:1.7.1",
```

Alternatively, you can [download the client Javascript](client/src/consent.js)
and save it with your web application source code.

The client script needs to be loaded on any page that could be an entry point to
your web application, allows modifying cookie consent, or provides a link to
another domain with which you want to share cookie consent status. It is
probably easiest to add the script to a base template used for all pages.

It is common practice to add Javascript tags just before the end `</body>` tag,
eg:

```html
    ...

    <script src="{path_to_client_js}/consent.js"></script>
  </body>
</html>
```


## Configuration

If you need to direct the client to an alternative API (for example, during
testing), you can add a `data-consent-api-url` attribute to the `body` tag in
your HTML file, eg:

```html
  <body data-consent-api-url="https://consent-api-nw.a.run.app/api/v1/consent/">
```


## Usage

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
Consent.onStatusLoaded((status) => {
  console.log("Consent Status:")
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
Consent.setStatus(
  acceptAllCookies,
  (status) => {
    console.log("Consent status successfully updated to", status)
  }
)
```

## Development

### Install

Clone the repository, then install dependencies with the following command:

```
make install
```

### Testing

#### Unit tests

Run unit tests with the following command:

```
make test
```

#### End-to-end tests

To run end-to-end tests you will need Chrome or Firefox installed. Specify which you
want to use for running tests by setting the `SELENIUM_DRIVER` environment variable
(defaults to `chrome`), eg:

```
export SELENIUM_DRIVER=firefox
```

You also need a running instance of the Consent API and instances of the [SDE Prototype
fake GOV.UK homepage](https://github.com/alphagov/sde-prototype-govuk) and [Hexagrams as
a Service](https://github.com/alphagov/sde-prototype-haas) webapps.

The tests expect to find these available at the following URLs:

| Name                   | Env var                  | Default                 |
| --                     | --                       | --                      |
| Consent API            | E2E_TEST_CONSENT_API_URL | http://localho.st:8000/ |
| Fake GOV.UK            | E2E_TEST_GOVUK_URL       | http://localho.st:8080/ |
| Hexagrams as a Service | E2E_TEST_HAAS_URL        | http://localho.st:8081  |

Due to CORS restrictions, the tests will fail if the URL domain is `localhost` or
`127.0.01`, so a workaround is to use `localho.st` which resolves to `127.0.0.1`.

Run the tests with the following command:

```
make test-end-to-end
```

### Branching

This project uses [Github Flow](https://githubflow.github.io/).

* `main` branch is always deployable
* To work on something new, create a descriptively named branch off `main`
* Commit to that branch locally and regularly push to the same named branch on the
  server (Github)
* When you need feedback or help, or you think the branch is ready to merge, rebase off
  `main` and open a pull request
* After the pull request has been reviewed and automated checks have passed, you can
  merge to `main`
* Commits to `main` are automatically built, deployed and tested in the Integration
  environment.

New features are developed on feature branches, which must be rebased on the main branch
and squashed before merging to main.
