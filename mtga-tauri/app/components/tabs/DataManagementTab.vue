<script setup lang="ts">
const store = useMtgaStore()

const handleOpen = () => {
  store.runPlaceholder("打开用户数据目录")
}

const handleBackup = () => {
  store.runPlaceholder("备份用户数据")
}

const handleRestore = () => {
  store.runPlaceholder("还原用户数据")
}

const handleClear = () => {
  store.runPlaceholder("清除用户数据")
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
