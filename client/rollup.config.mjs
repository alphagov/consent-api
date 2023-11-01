import typescript from '@rollup/plugin-typescript'
import terser from '@rollup/plugin-terser'

const baseConfig = {
  input: 'src/index.ts',
  plugins: [typescript()],
}

const unminifiedOutput = {
  format: 'iife',
  file: 'dist/singleconsent.js',
}

const minifiedOutput = {
  ...unminifiedOutput,
  file: 'dist/singleconsent.min.js',
  plugins: [terser()],
}

export default [
  { ...baseConfig, output: unminifiedOutput },
  { ...baseConfig, output: minifiedOutput },
]
