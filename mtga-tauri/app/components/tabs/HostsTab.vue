<script setup lang="ts">
const store = useMtgaStore()

const handleModify = () => {
  store.runPlaceholder("修改hosts文件")
}

const handleBackup = () => {
  store.runPlaceholder("备份hosts")
}

const handleRestore = () => {
  store.runPlaceholder("还原hosts")
}

const handleOpen = () => {
  store.runPlaceholder("打开hosts文件")
}
</script>

<template>
  <div class="space-y-3">
    <button class="btn btn-sm w-full" @click="handleModify">修改hosts文件</button>
    <div class="grid grid-cols-2 gap-2">
      <button class="btn btn-sm" @click="handleBackup">备份hosts</button>
      <button class="btn btn-sm" @click="handleRestore">还原hosts</button>
    </div>
    <button class="btn btn-sm w-full" @click="handleOpen">打开hosts文件</button>
  </div>
</template>
