import typescript from '@rollup/plugin-typescript'
import terser from '@rollup/plugin-terser'
import resolve from '@rollup/plugin-node-resolve'
import { babel } from '@rollup/plugin-babel'

const baseConfig = {
  input: 'src/index.ts',
}

let bundleConfig = [
  // ES Module format
  {
    ...baseConfig,
    output: {
      file: 'dist/singleconsent.esm.js',
      format: 'esm',
    },
    plugins: [typescript()],
  },
  // CommonJS format
  {
    ...baseConfig,
    output: {
      file: 'dist/singleconsent.cjs.js',
      format: 'cjs',
    },
    plugins: [typescript()],
  },
  // IIFE ES5 format (for direct usage in browser via a <script> tag)
  {
    ...baseConfig,
    output: {
      file: 'dist/singleconsent.iife.js',
      format: 'iife',
    },
    plugins: [typescript({ tsconfig: './tsconfig.es5.json' })],
  },
  // Minified IIFE ES5 format (for direct usage in browser via a <script> tag)
  {
    ...baseConfig,
    output: {
      file: 'dist/singleconsent.iife.min.js',
      format: 'iife',
    },
    plugins: [typescript({ tsconfig: './tsconfig.es5.json' }), terser()],
  },
]

bundleConfig = bundleConfig.map((config) => {
  config.plugins.unshift(
    // babel({
    //   babelHelpers: 'bundled',
    //   extensions: ['.js', '.ts'],
    // })
    babel({
      babelHelpers: 'bundled',
      presets: [
        [
          '@babel/preset-env',
          {
            useBuiltIns: 'usage',
            corejs: 3,
          },
        ],
      ],
    })
  )
  config.plugins.unshift(resolve())
  return config
})

export default bundleConfig
