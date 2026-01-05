<script setup lang="ts">
const store = useMtgaStore()

const handleGenerate = () => {
  store.runGenerateCertificates()
}

const handleInstall = () => {
  store.runInstallCaCert()
}

const handleClear = () => {
  store.runClearCaCert()
}
</script>

<template>
  <div class="mtga-soft-panel space-y-3">
    <div>
      <div class="text-sm font-semibold text-slate-900">证书管理</div>
      <div class="text-xs text-slate-500">生成、安装与清理本地证书</div>
    </div>
    <div class="space-y-2">
      <button class="btn btn-primary btn-sm w-full" @click="handleGenerate">
        生成CA和服务器证书
      </button>
      <div class="grid grid-cols-2 gap-2">
        <button class="btn btn-primary btn-sm" @click="handleInstall">安装CA证书</button>
        <button class="btn btn-outline btn-sm text-error hover:bg-error/10" @click="handleClear">
          清除系统CA证书
        </button>
      </div>
    </div>
  </div>
</template>
