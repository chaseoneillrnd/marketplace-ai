import nxPlugin from "@nx/eslint-plugin";
import tsParser from "@typescript-eslint/parser";

export default [
  {
    plugins: {
      "@nx": nxPlugin,
    },
  },
  {
    files: ["**/*.ts", "**/*.tsx"],
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        ecmaFeatures: { jsx: true },
      },
    },
    rules: {
      "@nx/enforce-module-boundaries": [
        "error",
        {
          enforceBuildableLibDependency: true,
          allow: ["design/tokens.json"],
          depConstraints: [
            {
              // Apps can only depend on libs, never on other apps
              sourceTag: "scope:app",
              onlyDependOnLibsWithTags: ["scope:lib"],
            },
            {
              // Libs can depend on other libs only
              sourceTag: "scope:lib",
              onlyDependOnLibsWithTags: ["scope:lib"],
            },
          ],
        },
      ],
    },
  },
  {
    ignores: [
      "node_modules/",
      "dist/",
      ".nx/",
      "apps/api/",
      "apps/mcp-server/",
      "libs/db/",
      "libs/python-common/",
      "apps/docs/",
    ],
  },
];
