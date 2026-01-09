<template>
  <div class="h-screen flex flex-col overflow-hidden bg-slate-50">
    <header class="w-full px-8 pt-8 shrink-0">
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

    <main class="w-full px-8 pt-6 pb-8 flex-1 min-h-0">
      <div class="grid grid-cols-12 gap-6 h-full">
        <!-- 左侧内容区 -->
        <section class="relative z-10 flex flex-col col-span-7 h-full min-h-0">
          <div class="flex-1 min-h-0">
            <slot name="left" />
          </div>
          
          <!-- 固定在左侧区域底部的操作栏，与上方保持固定间距 -->
          <div class="pt-6 shrink-0">
            <div class="mtga-card shadow-[0_-12px_30px_-10px_rgba(0,0,0,0.05)] backdrop-blur-lg bg-white/80">
              <div class="mtga-card-body py-4">
                <slot name="footer" />
              </div>
            </div>
          </div>
        </section>

        <!-- 右侧固定日志区 -->
        <section class="relative z-0 col-span-5 h-full min-h-0">
          <div class="h-full">
            <slot name="right" />
          </div>
        </section>
      </div>
    </main>

    <!-- 移除原有的全局 footer -->
  </div>
</template>
