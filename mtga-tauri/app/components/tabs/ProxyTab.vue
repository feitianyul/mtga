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
  <div class="space-y-3">
    <button class="btn btn-sm w-full" @click="handleStart">启动代理服务器</button>
    <button class="btn btn-sm w-full" @click="handleStop">停止代理服务器</button>
    <button class="btn btn-sm w-full" @click="handleCheck">检查网络环境</button>
  </div>
</template>
