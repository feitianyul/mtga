<template>
  <div class="min-h-screen">
    <header class="px-6 pt-6">
      <h1 class="text-2xl font-bold">
        <slot name="title">MTGA - 代理服务器管理工具</slot>
      </h1>
      <slot name="subtitle" />
    </header>

    <main class="px-6 py-4">
      <div class="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <section class="space-y-4">
          <slot name="left" />
        </section>
        <section class="space-y-4">
          <slot name="right" />
        </section>
      </div>
    </main>

    <footer class="px-6 pb-6">
      <slot name="footer" />
    </footer>
  </div>
</template>
