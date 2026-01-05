<script setup lang="ts">
const { appInfo, runCheckUpdates } = useMtgaStore()

const handleCheckUpdates = () => {
  runCheckUpdates()
}
</script>

<template>
  <div class="mtga-soft-panel space-y-3">
    <div>
      <div class="text-sm font-semibold text-slate-900">
        {{ appInfo.display_name }} {{ appInfo.version }}
      </div>
      <div class="text-xs text-slate-500">关于与更新信息</div>
    </div>
    <button class="btn btn-outline btn-sm w-fit" @click="handleCheckUpdates">检查更新</button>
    <div class="text-xs text-slate-400">powered by BiFangKNT</div>
  </div>
</template>
