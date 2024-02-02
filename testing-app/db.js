const fs = require("fs");

const DB_FILE = "db.json";

const getDb = () => {
  if (fs.existsSync(DB_FILE)) {
    return JSON.parse(fs.readFileSync(DB_FILE, "utf-8"));
  } else {
    // create the db
    fs.writeFileSync(DB_FILE, "{}");
  }
};

const createConsents = (uid, consents) => {
  const db = getDb();
  console.log("db", db);
  db[uid] = consents;
  fs.writeFileSync(DB_FILE, JSON.stringify(db));
};

const updateConsents = (uid, consents) => {
  const db = getDb();
  db[uid] = consents;
  fs.writeFileSync(DB_FILE, JSON.stringify(db));
};

const getConsents = (uid) => {
  const db = getDb();
  return db[uid] || null;
};

module.exports = {
  createConsents,
  updateConsents,
  getConsents,
};
