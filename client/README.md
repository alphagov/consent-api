# Cookie Consent Sharing API client

This script contains the code you need to integrate with the Cookie Consent Sharing API,
to share users' consent to cookies across domains.

## Contact the team

The Cookie Consent Sharing API is maintaine by a team at Government Digital Service. If
you want to know more about the API, please email the Data Infrastructure team or get in
touch with them on Slack.

## Quick start

There are 2 ways to start using the Cookie Consent Sharing API in your app.

### 1. Install with npm (recommended)

We recommend installing the Cookie Consent Sharing API client using node package manager
(npm).

### 2. Install by using compiled files

You can also download the compiled and minified Javascript from Github.

## Importing Javascript

You can include the Javascript for the API client by copying the `consent_api.js` from
`node_modules/@alphagov/consent_api/` into your application or referencing the file
directly:

```html
<script src="<path-to-consent-api-js-file>/consent_api.js"></script>
```

Next you need to initialise the script by adding:

```html
<script>window.SharedCookieConsent.init()</script>
```

## Getting updates

To be notified when there's a new release, you can watch the consent-api Github
repository.

Find out how to update with npm.

## License

Unless stated otherwise, the codebase is released under the MIT License. This covers
both the codebase and any sample code in the documentation. The documentation is &copy;
Crown copyright and availabe under the terms of the Open Government 3.0 licence.

## Contribution guidelines

If you want to help us build the Cookie Consent Sharing API, view our contribution
guidelines.
