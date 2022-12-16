const path = require('path')

module.exports = {
  mode: 'development',
  devtool: 'inline-source-map',
  entry: [
    './client/src/utils.js',
    './client/src/cookie-banner.js',
    './client/src/cookies-page.js',
    './client/src/consent.js'
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
    filename: 'consent.js',
    path: path.resolve(__dirname, 'client/dist')
  }
}
