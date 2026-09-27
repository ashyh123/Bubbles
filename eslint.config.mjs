import { defineConfig, globalIgnores } from 'eslint/config';
import nextVitals from 'eslint-config-next/core-web-vitals';
import nextTs from 'eslint-config-next/typescript';
import prettier from 'eslint-config-prettier/flat';

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  prettier,
  globalIgnores([
    '.next/**',
    'out/**',
    'build/**',
    'next-env.d.ts',
    'coverage/**',
    'supabase/.temp/**',
  ]),
  {
    rules: {
      'no-console': 'error',
    },
  },
  {
    files: ['src/lib/privacy/log.ts', 'src/**/*.test.ts'],
    rules: {
      'no-console': 'off',
    },
  },
]);

export default eslintConfig;
