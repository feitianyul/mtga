<script setup lang="ts">
defineProps<{
  open?: boolean
  title?: string
}>()
</script>

<template>
  <dialog class="modal" :open="open">
    <div class="modal-box">
      <h3 class="text-lg font-bold">{{ title || '确认操作' }}</h3>
      <div class="mt-3 text-sm">
        <slot>请确认是否继续该操作。</slot>
      </div>
      <div class="modal-action">
        <button class="btn">取消</button>
        <button class="btn btn-primary">确认</button>
      </div>
    </div>
  </dialog>
</template>
