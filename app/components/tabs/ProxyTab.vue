<script setup lang="ts">
const store = useMtgaStore()

const handleStart = () => {
  store.runProxyStart()
}

const handleStop = () => {
  store.runProxyStop()
}

const handleCheck = () => {
  store.runProxyCheckNetwork()
}
</script>

<template>
  <div class="mtga-soft-panel space-y-3">
    <div>
      <div class="text-sm font-semibold text-slate-900">代理服务</div>
      <div class="text-xs text-slate-500">启动 / 停止 / 网络检查</div>
    </div>
    <div class="space-y-2">
      <button class="btn btn-primary btn-sm w-full rounded-xl shadow-sm" @click="handleStart">启动代理服务器</button>
      <button class="btn btn-outline btn-sm rounded-xl border-slate-200 text-error hover:bg-error/10 hover:border-error w-full" @click="handleStop">停止代理服务器</button>
      <button class="btn btn-outline btn-sm rounded-xl border-slate-200 hover:border-amber-500 hover:bg-amber-50/50 hover:text-amber-600 w-full" @click="handleCheck">检查网络环境</button>
    </div>
  </div>
</template>
