const { v4 } = require("uuid");

const db = {};

module.exports = function (app) {
  app.get("/", (req, res) => {
    res.send("<h1>Hello world</h1>");
  });

  app.get("/timeout", (req, res) => {
    setTimeout(() => {
      res.send("<h1>Timeout</h1>");
    }, 5000);
  });

  app.get("/api/v1/origins", (req, res) => {
    res.send([]);
  });

  app.get("/api/v1/consent/:uid", (req, res) => {
    const { uid } = req.params;
    setTimeout(() => {
      res.send({ consents: db[uid] || null });
    }, 10000);
  });

  app.post("/api/v1/consent/:uid", (req, res) => {
    const { uid: paramId } = req.params;
    const consents = JSON.parse(req.body.status);

    const uid = paramId || v4();

    db[uid] = consents;

    setTimeout(() => {
      res.send({ uid, consents });
    }, 10000);
    // res.send({uid, consents})
  });

  app.post("/api/v1/consent", (req, res) => {
    const consents = JSON.parse(req.body.status);
    const uid = v4();

    db[uid] = consents;

    setTimeout(() => {
      res.send({ uid, consents });
    }, 10000);
    // res.send({uid, consents})
  });
};
