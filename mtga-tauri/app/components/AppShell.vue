<template>
  <div class="min-h-screen">
    <header class="mx-auto max-w-[1400px] px-6 pt-8">
      <div class="mtga-card">
        <div class="mtga-card-body">
          <div class="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p class="text-xs uppercase tracking-[0.22em] text-slate-400">
                MTGA Console
              </p>
              <h1 class="mt-2 text-2xl font-semibold tracking-tight text-slate-900">
                <slot name="title">MTGA - 代理服务器管理工具</slot>
              </h1>
              <div class="mt-2 text-sm text-slate-500">
                <slot name="subtitle">一站式代理与证书管理面板</slot>
              </div>
            </div>
            <div class="flex flex-wrap items-center gap-2">
              <slot name="meta">
                <span class="mtga-chip">本地控制台</span>
                <span class="mtga-chip">实时配置</span>
              </slot>
            </div>
          </div>
        </div>
      </div>
    </header>

    <main class="mx-auto max-w-[1400px] px-6 py-6">
      <div class="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <section class="relative z-10 space-y-6">
          <slot name="left" />
        </section>
        <section class="relative z-0 space-y-6 xl:sticky xl:top-6">
          <slot name="right" />
        </section>
      </div>
    </main>

    <footer class="mx-auto max-w-[1400px] px-6 pb-8">
      <div class="mtga-card">
        <div class="mtga-card-body">
          <slot name="footer" />
        </div>
      </div>
    </footer>
  </div>
</template>
