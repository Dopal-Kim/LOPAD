import js from '@eslint/js';
import tseslint from 'typescript-eslint';
import prettier from 'eslint-config-prettier';
import globals from 'globals';

export default tseslint.config(
  { ignores: ['dist/', 'node_modules/', '.claude/', 'parts/'] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  prettier,
  {
    files: ['src/**/*.ts'],
    languageOptions: { globals: { ...globals.browser } },
    rules: {
      '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    },
  },
  // 파트 격리 (루트 CLAUDE.md 3장, 계약 ui-system-interface.md): UI 파트는 계약 파일과 phaser 만 import
  {
    files: ['src/ui/**/*.ts'],
    rules: {
      'no-restricted-imports': [
        'error',
        {
          patterns: [
            {
              group: [
                '**/core/*',
                '**/systems/*',
                '**/data/*',
                '**/scenes/*',
                '**/objects/*',
                '**/world/*',
                '**/debug/*',
                '**/contract/host',
                '**/contract/snapshot',
              ],
              message: 'UI 파트는 src/contract/ui.ts 와 phaser 만 import 할 수 있습니다 (계약 §6).',
            },
          ],
        },
      ],
    },
  },
  // 시스템 파트는 UI 의 index 만 import
  {
    files: ['src/**/*.ts'],
    ignores: ['src/ui/**/*.ts'],
    rules: {
      'no-restricted-imports': [
        'error',
        {
          patterns: [
            {
              group: ['**/ui/*', '!**/ui/index'],
              message: '시스템 파트는 src/ui/index.ts 만 import 할 수 있습니다 (계약 §5).',
            },
          ],
        },
      ],
    },
  },
);
