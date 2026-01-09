<script setup lang="ts">
const store = useMtgaStore()
const appInfo = store.appInfo

const openDirTooltip = computed(() => {
  const current = appInfo.value.user_data_dir?.trim()
  const fallback = appInfo.value.default_user_data_dir?.trim()
  if (current && fallback && current !== fallback) {
    return `使用系统文件管理器打开用户数据目录\n当前：${current}\n默认：${fallback}`
  }
  if (current) {
    return `使用系统文件管理器打开用户数据目录\n目录：${current}`
  }
  if (fallback) {
    return `使用系统文件管理器打开用户数据目录\n默认目录：${fallback}`
  }
  return "使用系统文件管理器打开用户数据目录"
})
const backupTooltip = [
  "创建带时间戳的完整数据备份",
  "备份内容：配置文件、SSL证书、hosts备份",
  "备份位置：用户数据目录/backups/backup_时间戳/",
].join("\n")
const restoreTooltip = [
  "从最新备份恢复用户数据（覆盖现有数据）",
  "自动选择最新时间戳的备份进行还原",
  "注意：此操作会覆盖当前的配置和证书",
].join("\n")
const clearTooltip = [
  "删除所有用户数据（保留历史备份）",
  "清除内容：配置文件、SSL证书、hosts备份",
  "保留内容：backups文件夹及其历史备份",
].join("\n")

const handleOpen = () => {
  store.runUserDataOpenDir()
}

const handleBackup = () => {
  store.runUserDataBackup()
}

const handleRestore = () => {
  store.runUserDataRestoreLatest()
}

const handleClear = () => {
  store.runUserDataClear()
}
</script>

<template>
  <div class="mtga-soft-panel space-y-3">
    <div>
      <div class="text-sm font-semibold text-slate-900">用户数据</div>
      <div class="text-xs text-slate-500">备份与恢复历史数据</div>
    </div>
    <div class="space-y-2">
      <button
        class="btn btn-outline btn-sm w-full tooltip mtga-tooltip"
        :data-tip="openDirTooltip"
        @click="handleOpen"
      >
        打开目录
      </button>
      <button
        class="btn btn-primary btn-sm w-full tooltip mtga-tooltip"
        :data-tip="backupTooltip"
        style="--mtga-tooltip-max: 360px;"
        @click="handleBackup"
      >
        备份数据
      </button>
      <button
        class="btn btn-outline btn-sm w-full tooltip mtga-tooltip"
        :data-tip="restoreTooltip"
        style="--mtga-tooltip-max: 360px;"
        @click="handleRestore"
      >
        还原数据
      </button>
      <button
        class="btn btn-outline btn-sm w-full text-error hover:bg-error/10 tooltip mtga-tooltip"
        :data-tip="clearTooltip"
        style="--mtga-tooltip-max: 360px;"
        @click="handleClear"
      >
        清除数据
      </button>
    </div>
  </div>
</template>
