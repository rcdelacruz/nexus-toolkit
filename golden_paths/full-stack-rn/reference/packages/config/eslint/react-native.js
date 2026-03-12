import baseConfig from "./base.js"

export default [
  ...baseConfig,
  {
    rules: {
      "no-console": "warn",
      "@typescript-eslint/no-require-imports": "off",
    },
  },
]
