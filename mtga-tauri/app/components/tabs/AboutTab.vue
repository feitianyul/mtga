<script setup lang="ts">
const { appInfo, runPlaceholder } = useMtgaStore()

const handleCheckUpdates = () => {
  runPlaceholder("检查更新")
}
</script>

<template>
  <div class="space-y-3">
    <div class="text-base font-semibold">
      {{ appInfo.display_name }} {{ appInfo.version }}
    </div>
    <button class="btn btn-sm" @click="handleCheckUpdates">检查更新</button>
    <div class="text-xs text-base-content/60">powered by BiFangKNT</div>
  </div>
</template>
