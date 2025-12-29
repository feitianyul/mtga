<script setup lang="ts">
const store = useMtgaStore()

const handleStartAll = () => {
  store.runProxyStartAll()
}
</script>

<template>
  <div class="flex items-center justify-end">
    <button class="btn btn-primary" @click="handleStartAll">一键启动全部服务</button>
  </div>
</template>
