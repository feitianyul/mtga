<script setup lang="ts">
const store = useMtgaStore()

const handleStart = () => {
  store.runPlaceholder("启动代理服务器")
}

const handleStop = () => {
  store.runPlaceholder("停止代理服务器")
}

const handleCheck = () => {
  store.runPlaceholder("检查网络环境")
}
</script>

<template>
  <div class="space-y-3">
    <button class="btn btn-sm w-full" @click="handleStart">启动代理服务器</button>
    <button class="btn btn-sm w-full" @click="handleStop">停止代理服务器</button>
    <button class="btn btn-sm w-full" @click="handleCheck">检查网络环境</button>
  </div>
</template>
