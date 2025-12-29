<script setup lang="ts">
const store = useMtgaStore()

const handleGenerate = () => {
  store.runPlaceholder("生成CA和服务器证书")
}

const handleInstall = () => {
  store.runPlaceholder("安装CA证书")
}

const handleClear = () => {
  store.runPlaceholder("清除系统CA证书")
}
</script>

<template>
  <div class="space-y-3">
    <button class="btn btn-sm w-full" @click="handleGenerate">生成CA和服务器证书</button>
    <button class="btn btn-sm w-full" @click="handleInstall">安装CA证书</button>
    <button class="btn btn-sm w-full" @click="handleClear">清除系统CA证书</button>
  </div>
</template>
