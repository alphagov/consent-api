# Single Consent

The Single Consent service enables easily sharing a user's consent or rejection
of cookies across different websites. This ensures a seamless user experience by
remembering a user's preferences without repeatedly asking for consent.

## How does it work?

1. **Cookie Consent**: When you visit a Single Consent enabled website, you may
   encounter a pop-up or banner asking for your consent to use cookies.

2. **Unique ID**: If you respond, your consent to (or refusal of) cookies is
   then submitted to the Single Consent service, which assigns you a randomly
   generated unique ID. This ID does not contain any personal information about
   you.

3. **Central Database**: Your consent data is then associated with your unique
   ID and stored in the central Single Consent database.

4. **Javascript Client**: The website receives your unique ID via the Single
   Consent client, a small piece of Javascript code embedded in the website.

5. **Link Decoration**: The client automatically appends your
   unique ID as a parameter to the links you click on which lead to other
   Single Consent enabled websites.

6. **Consent Lookup**: When a Single Consent enabled website receives a request
   with a URL containing your unique ID, it uses this ID to look up your consent
   data in the central database. Using this data, the website can respect your
   preferences and avoid asking for consent again.

7. **Revoking Consent**: If you change your mind and refuse (or grant) consent
   to use cookies, you can modify your cookie settings on the current website
   and it will submit the updated data to the central database, making all other
   Single Consent enabled websites aware of your changed preferences.

8. **ID Cookie**: The Single Consent client also stores your unique ID in a
   cookie for the current website, so that if you return to the site without
   clicking a link (eg via a bookmark, or typing in the URL to the address bar
   in your browser), your consent preferences will be remembered.

## Installation

To make use of the Single Consent service on your website, please see the
[Single Consent client Quick Start documentation](client/README.md)

#### Environment variables

- `DATABASE_URL` (default is `postgresql+asyncpg://localhost:5432/consent_api`)
- `ENV` (default is `development`)
- `PORT` (default is `8000`)
- `SECRET_KEY` (default is randomly generated)
- You can configure the number of web server worker processes with the
  `WEB_CONCURRENCY` environment variable (default is 1)

## Development

You can run all the services without setup needed:

```shell
make docker-build
docker compose up
```

### Loading the environment with direnv

When running docker commands, you will need a few extra environment variables.

It's easiest to use [Direnv](https://direnv.net/) to load the environment.

Copy `.envrc.template` to `.envrc` and load it with direnv:

```shell
direnv allow
```

Those variables will be used by both docker-compose and the Makefile.

Additionally, we recommend [hooking direnv with your shell](https://direnv.net/docs/hook.html), for automatic environment loading.

### Run Locally

To run the API locally:

```shell
make install
make run
```

It will install poetry, our python dependencies manager, as well as the project dependencies.

### Testing

#### Unit tests

Run unit tests with the following command:

```sh
make test
```

#### End-to-end tests

##### Running in Docker Compose

You will need to build a Docker image to run the tests against, using the
following command:

```sh
make docker-build
```

You also need to have the Chrome Docker image already on your system, which you
can do with the following command:

```sh
docker pull selenoid/chrome:110.0
```

> **Note**
> Currently, Selenoid does not provide a Chrome image that works on Apple M1 hosts. As a
> workaround, you can use a third-party Chromium image:
>
> ```sh
> docker pull sskorol/selenoid_chromium_vnc:100.0
> ```
>
> Then set the following environment variable:
>
> ```sh
> export SPLINTER_REMOTE_BROWSER_VERSION=sskorol/selenoid_chromium_vnc:100.0
> ```

The easiest way to run the end-to-end tests is in Docker Compose using the following
command:

```sh
make test-end-to-end-docker
```

##### Running locally

To run end-to-end tests you will need Chrome or Firefox installed. Specify which you
want to use for running tests by setting the `SELENIUM_DRIVER` environment variable
(defaults to `chrome`), eg:

```sh
export SELENIUM_DRIVER=firefox
```

You also need a running instance of the Consent API and two instances of webapps
which have the Single Consent client installed.

> Note
> For convenience, a dummy service is included in the API.
> You can run two more instances of the Consent API on different port numbers to
> act as dummy services:
>
> ```sh
> CONSENT_API_ORIGIN=http://localho.st:8000 OTHER_SERVICE_ORIGIN=http://localho.st:8082 PORT=8081 make run
> ```
>
> and
>
> ```sh
> CONSENT_API_ORIGIN=http://localho.st:8000 PORT=8082 make run
> ```

The tests expect to find these available at the following URLs:

| Name            | Env var                      | Default                |
| --------------- | ---------------------------- | ---------------------- |
| Consent API     | E2E_TEST_CONSENT_API_URL     | http://localho.st:8000 |
| Dummy service 1 | E2E_TEST_DUMMY_SERVICE_1_URL | http://localho.st:8080 |
| Dummy service 2 | E2E_TEST_DUMMY_SERVICE_2_URL | http://localho.st:8081 |

Due to CORS restrictions, the tests will fail if the URL domain is `localhost` or
`127.0.01`, so a workaround is to use `localho.st` which resolves to `127.0.0.1`.

Run the tests with the following command:

```
make test-end-to-end
```

### Branching

This project uses [Github Flow](https://githubflow.github.io/).

- `main` branch is always deployable
- To work on something new, create a descriptively named branch off `main`
- Commit to that branch locally and regularly push to the same named branch on the
  server (Github)
- When you need feedback or help, or you think the branch is ready to merge, rebase off
  `main` and open a pull request
- After the pull request has been reviewed and automated checks have passed, you can
  merge to `main`
- Commits to `main` are automatically built, deployed and tested in the Integration
  environment.

New features are developed on feature branches, which must be rebased on the main branch
and squashed before merging to main.

## License

Unless stated otherwise, the codebase is released under the MIT License. This covers
both the codebase and any sample code in the documentation. The documentation is &copy;
Crown copyright and availabe under the terms of the Open Government 3.0 licence.

## Contact the team

The Single Consent service is maintained by a team at Government Digital
Service. If you want to know more about the service, please email the Data
Infrastructure team or get in touch with them on Slack.

Team email:
`data-tools-alerts@digital.cabinet-office.gov.uk`

You can also contact the maintainers of this repository via email:

- Guilhem Forey: `guilhem.forey@digital.cabinet-office.gov.uk`
