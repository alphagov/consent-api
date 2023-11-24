import typescript from '@rollup/plugin-typescript'
import terser from '@rollup/plugin-terser'

const baseConfig = {
  input: 'src/index.ts',
  plugins: [typescript()],
}

const bundleConfig = [
  // ES Module format
  {
    ...baseConfig,
    output: {
      file: 'dist/singleconsent.esm.js',
      format: 'esm',
    },
  },
  // CommonJS format
  {
    ...baseConfig,
    output: {
      file: 'dist/singleconsent.cjs.js',
      format: 'cjs',
    },
  },
  // IIFE ES5 format (for direct usage in browser via a <script> tag)
  {
    ...baseConfig,
    output: {
      file: 'dist/singleconsent.iife.js',
      format: 'iife',
    },
  },
  // Minified IIFE ES5 format (for direct usage in browser via a <script> tag)
  {
    ...baseConfig,
    output: {
      file: 'dist/singleconsent.iife.min.js',
      format: 'iife',
      plugins: [terser()],
    },
  },
]

export default bundleConfig
