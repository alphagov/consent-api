const { v4 } = require("uuid");
const db = require("./db");

const DELAYS = {
  // setConsents: true,
  // getConsents: true,
  // timeout: true,
  // origins: true,
};

const DELAY_MS = 11000;

module.exports = function (app) {
  app.get("/", (req, res) => {
    res.send("<h1>Hello world</h1>");
  });

  app.get("/timeout", (req, res) => {
    if (DELAYS.timeout) {
      setTimeout(() => {
        res.send("<h1>Timeout</h1>");
      }, DELAY_MS);
    } else {
      res.send("<h1>Timeout</h1>");
    }
  });

  app.get("/api/v1/origins", (req, res) => {
    if (DELAYS.origins) {
      setTimeout(() => {
        res.send(["http://localhost:3000"]);
      }, DELAY_MS);
    } else {
      res.send(["http://localhost:3000"]);
    }
  });

  app.get("/api/v1/consent/:uid", (req, res) => {
    const { uid } = req.params;
    const consents = db.getConsents(uid);

    if (DELAYS.getConsents) {
      setTimeout(() => {
        res.send({ consents });
      }, DELAY_MS);
    } else {
      res.send({ consents });
    }
  });

  app.post("/api/v1/consent/:uid", (req, res) => {
    const { uid: paramId } = req.params;
    const consents = JSON.parse(req.body.status);

    const uid = paramId || v4();

    db.updateConsents(uid, consents);

    if (DELAYS.setConsents) {
      setTimeout(() => {
        res.send({ uid, consents });
      }, DELAY_MS);
    } else {
      res.send({ uid, consents });
    }
  });

  app.post("/api/v1/consent", (req, res) => {
    const consents = JSON.parse(req.body.status);
    const uid = v4();

    db.createConsents(uid, consents);

    if (DELAYS.setConsents) {
      setTimeout(() => {
        res.send({ uid, consents });
      }, DELAY_MS);
    } else {
      res.send({ uid, consents });
    }
  });
};
