<script setup lang="ts">
const store = useMtgaStore()

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
      <button class="btn btn-outline btn-sm w-full" @click="handleOpen">打开目录</button>
      <button class="btn btn-primary btn-sm w-full" @click="handleBackup">备份数据</button>
      <button class="btn btn-outline btn-sm w-full" @click="handleRestore">还原数据</button>
      <button class="btn btn-outline btn-sm w-full text-error hover:bg-error/10" @click="handleClear">
        清除数据
      </button>
    </div>
  </div>
</template>
