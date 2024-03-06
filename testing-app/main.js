const express = require("express");
const cors = require("cors");
const mockApp = require("./apiMock");

const app = express();
const port = 3000;

app.use(cors());
app.use(express.urlencoded({ extended: true }));

mockApp(app);

app.listen(port, () => {
  console.log(`Example app listening at http://localhost:${port}`);
});
