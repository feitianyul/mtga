import tailwindcss from "@tailwindcss/vite";
// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  components: [{ path: './app/components', pathPrefix: false }],
  // 启用 SSG
  ssr: false,
  // 使开发服务器能够被其他设备发现，以便在 iOS 物理机运行。
  devServer: { host: process.env.TAURI_DEV_HOST || 'localhost' },
  vite: {
    // 为 Tauri 命令输出提供更好的支持
    clearScreen: false,
    // 启用环境变量
    // 其他环境变量可以在如下网页中获知：
    // https://v2.tauri.app/reference/environment-variables/
    envPrefix: ['VITE_', 'TAURI_'],
    server: {
      // Tauri需要一个确定的端口
      strictPort: true,
    },
    plugins: [tailwindcss()],
  },
  css: ["./app/assets/css/tailwind.css"],
  ignore: ['**/src-tauri/**']
})
