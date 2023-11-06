import typescript from '@rollup/plugin-typescript'

export default {
  input: 'src/index.ts',
  output: {
    format: 'iife',
    file: 'dist/singleconsent.js',
  },
  plugins: [typescript()],
}
