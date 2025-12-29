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
  <div class="space-y-3">
    <button class="btn btn-sm w-full" @click="handleOpen">打开目录</button>
    <button class="btn btn-sm w-full" @click="handleBackup">备份数据</button>
    <button class="btn btn-sm w-full" @click="handleRestore">还原数据</button>
    <button class="btn btn-sm w-full" @click="handleClear">清除数据</button>
  </div>
</template>
