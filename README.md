# Single Consent API

This is a HTTP API and simple frontend app, which holds user consent to cookies in a
central database.

This enables web services to share user consent status across multiple domains.


## Testing

### Unit tests

Run unit tests with the following command:

```
pytest -m unit
```

### Integration tests

Run integration tests with the following command:

```
pytest -m integration
```

### End-to-end tests

To run end-to-end tests you will need Chrome or Firefox installed. Specify which you
want to use for running tests by setting the `SELENIUM_DRIVER` environment variable, eg:

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
pytest --splinter-driver $SELENIUM_DRIVER --splinter-headless -m end_to_end
```

## Contributing

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
