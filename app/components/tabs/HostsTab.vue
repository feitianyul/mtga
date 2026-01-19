<script setup lang="ts">
const store = useMtgaStore()

const handleModify = () => {
  store.runHostsModify("add")
}

const handleBackup = () => {
  store.runHostsModify("backup")
}

const handleRestore = () => {
  store.runHostsModify("restore")
}

const handleOpen = () => {
  store.runHostsOpen()
}
</script>

<template>
  <div class="mtga-soft-panel space-y-3">
    <div>
      <div class="text-sm font-semibold text-slate-900">hosts 文件</div>
      <div class="text-xs text-slate-500">快速修改与备份恢复</div>
    </div>
    <div class="space-y-2">
      <button class="btn btn-primary btn-sm w-full rounded-xl shadow-sm" @click="handleModify">修改hosts文件</button>
      <div class="grid grid-cols-2 gap-2">
        <button class="btn btn-outline btn-sm rounded-xl border-slate-200 hover:border-amber-500 hover:bg-amber-50/50 hover:text-amber-600" @click="handleBackup">备份hosts</button>
        <button class="btn btn-outline btn-sm rounded-xl border-slate-200 hover:border-amber-500 hover:bg-amber-50/50 hover:text-amber-600" @click="handleRestore">还原hosts</button>
      </div>
      <button class="btn btn-outline btn-sm w-full rounded-xl border-slate-200 hover:border-amber-500 hover:bg-amber-50/50 hover:text-amber-600" @click="handleOpen">打开hosts文件</button>
    </div>
  </div>
</template>
