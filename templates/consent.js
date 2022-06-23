!function () {
  "use strict";

  var Consent = window.Consent = window.Consent || {};

  Consent.crossOriginUID = new URL(window.location.href).searchParams.get("uid");
  Consent.consentShared = !!Consent.crossOriginUID;
  Consent.originUID = "{{ uid }}";
  Consent.originStatus = "{{ consent_status }}";
  Consent.uid = Consent.consentShared ? Consent.crossOriginUID : Consent.originUID;
  Consent.apiURL = "{{ api_url }}/" + Consent.uid;

  Consent.status = Consent.originStatus;

  Consent.init = function () {
    this.cookieBanner = document.querySelector(".cookie-banner");
    this.cookiePrompt = this.cookieBanner.querySelector(".prompt");
    this.grant = this.cookieBanner.querySelector(".grant");
    this.revoke = this.cookieBanner.querySelector(".revoke");
    this.initCookieBanner();

    this.getStatus()
      .then(status => {
        this.cookieBanner.style.display = "block";
        this.showBannerContent(status);
        this.decorateLinks();
        this.updateDisplay();
      });
  };

  Consent.showBannerContent = function (status) {
    Object.entries({
      'None': this.cookiePrompt,
      'CONSENT': this.revoke,
      'NO_CONSENT': this.grant,
    }).forEach(([key, el]) => {
      if (key === status) {
        el.hidden = false;
        el.style.display = "block";
      } else {
        el.hidden = true;
        el.style.display = "none";
      }
    });
  };

  Consent.getStatus = async function () {
    if (this.consentShared) {
      this.status = await fetch(this.apiURL, {cache: 'no-cache'})
        .then(r => r.json())
        .then(data => data.status);
    }
    return this.status;
  };

  Consent.setStatus = function (status) {
    return fetch(this.apiURL, {
      method: 'POST',
      cache: 'no-cache',
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: 'status=' + status + '&uid=' + this.uid
    })
      .then(() => {
        this.status = status;
        this.updateDisplay();
      });
  };

  Consent.updateDisplay = function () {
    for (var el of document.querySelectorAll(".consent-uid")) {
      el.innerText = Consent.uid;
    }
    for (var el of document.querySelectorAll('.consent-status')) {
      el.innerText = Consent.status;
    }
  };

  Consent.decorateLinks = function () {
    for (var link of document.querySelectorAll("[data-consent-share]")) {
      link.addEventListener("click", (e) => {
        var link = e.target;
        var url = new URL(link.href);
        url.searchParams.append("uid", this.uid);
        link.href = url.href;
      });
    }
  };

  Consent.initCookieBanner = function () {
    for (var el of document.querySelectorAll("[data-accept-cookies]")) {
      el.addEventListener("click", (e) => {
        this.setStatus('CONSENT')
          .then(this.showBannerContent('CONSENT'));
      });
    }
    for (var el of document.querySelectorAll("[data-reject-cookies]")) {
      el.addEventListener("click", (e) => {
        this.setStatus('NO_CONSENT')
          .then(this.showBannerContent('NO_CONSENT'));
      });
    }
  };
}();
