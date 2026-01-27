<script setup lang="ts">
const store = useMtgaStore()
const appInfo = store.appInfo

const clearCaTooltip = computed(() => {
  const commonName = appInfo.value.ca_common_name || "MTGA_CA"
  return [
    "macOS: 删除系统钥匙串中匹配的CA证书；",
    "Windows: 删除本地计算机/Root 中匹配的CA证书",
    `Common Name: ${commonName}`,
    "需要管理员权限，建议仅在需要重置证书时使用",
  ].join("\n")
})

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
      <button class="mtga-btn-primary" @click="handleGenerate">
        生成CA和服务器证书
      </button>
      <div class="grid grid-cols-2 gap-2">
        <button class="mtga-btn-primary" @click="handleInstall">安装CA证书</button>
        <button
          class="mtga-btn-error tooltip mtga-tooltip"
          :data-tip="clearCaTooltip"
          style="--mtga-tooltip-max: 280px;"
          @click="handleClear"
        >
          清除系统CA证书
        </button>
      </div>
    </div>
  </div>
</template>
