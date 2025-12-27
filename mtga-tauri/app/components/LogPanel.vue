<template>
  <div class="card bg-base-200 shadow-sm">
    <div class="card-body p-4">
      <h2 class="card-title text-base">日志</h2>
      <div
        class="mt-2 h-80 overflow-auto rounded bg-base-100 p-3 text-sm font-mono text-base-content/80"
      >
        <slot>日志输出占位</slot>
      </div>
    </div>
  </div>
</template>
