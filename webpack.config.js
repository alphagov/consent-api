const path = require('path');

module.exports = {
  mode: 'development',
  devtool: 'inline-source-map',
  entry: [
    './consent_api/client/src/utils.js',
    './consent_api/client/src/cookie-banner.js',
    './consent_api/client/src/cookies-page.js',
    './consent_api/client/src/consent.js'
  ],
  module: {
    rules: [{
      test: /\.js$/,
      exclude: /node_modules/,
      use: {
        loader: 'babel-loader',
        options: {
          presets: ['@babel/preset-env']
        }
      }
    }]
  },
  output: {
    filename: "consent.js",
    path: path.resolve(__dirname, 'consent_api/client/dist'),
  }
};
