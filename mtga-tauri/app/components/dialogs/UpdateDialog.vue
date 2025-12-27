<script setup lang="ts">
defineProps<{
  open?: boolean
  versionLabel?: string
}>()
</script>

<template>
  <dialog class="modal" :open="open">
    <div class="modal-box">
      <h3 class="text-lg font-bold">发现新版本{{ versionLabel ? `：${versionLabel}` : '' }}</h3>
      <div class="mt-3 rounded bg-base-200 p-3 text-sm">
        Release notes 占位（HTML 内容后续注入）
      </div>
      <div class="modal-action">
        <button class="btn">关闭</button>
        <button class="btn btn-primary">前往发布页</button>
      </div>
    </div>
  </dialog>
</template>
