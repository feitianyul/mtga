import withNuxt from "./.nuxt/eslint.config.mjs"
import betterTailwind from "eslint-plugin-better-tailwindcss"

export default withNuxt(
  {
    ignores: [
      "node_modules",
      ".nuxt",
      ".output",
      "dist",
      "src-tauri",
      "python-src",
    ],
  },
  {
    files: ["**/*.{ts,tsx,vue}"],
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: process.cwd(),
      },
    },
    rules: {
      "@typescript-eslint/no-unsafe-type-assertion": "warn",
      "@typescript-eslint/no-unnecessary-type-assertion": "warn",
    },
  },
  // 添加 Better Tailwind CSS 支持
  {
    plugins: {
      "better-tailwindcss": betterTailwind,
    },
    rules: {
      // 使用 warn 级别而不是 error，避免阻塞开发
      ...Object.fromEntries(
        Object.entries(betterTailwind.configs.recommended.rules).map(([key, value]) => [
          key,
          value === "error" ? "warn" : value,
        ])
      ),
      "better-tailwindcss/no-unregistered-classes": "off", // daisyUI 类名经常被识别为未注册，暂时关闭
      "better-tailwindcss/enforce-consistent-class-order": "off", // 排序规则太严格，暂时关闭
      "better-tailwindcss/enforce-consistent-line-wrapping": "off", // 换行规则太严格，暂时关闭
      "vue/multi-word-component-names": "off", // 允许单单词组件名
      "vue/html-self-closing": "off", // 允许在 HTML void elements 上使用自闭合
      "@typescript-eslint/unified-signatures": "off", // 允许分开定义重载（在 defineEmits 中常见）
    },
    settings: {
      "better-tailwindcss": {
        // Tailwind v4 的 CSS 入口文件
        entryPoint: "app/assets/css/tailwind.css",
      },
    },
  }
)
