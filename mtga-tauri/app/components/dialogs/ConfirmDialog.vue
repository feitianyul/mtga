<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    open?: boolean
    title?: string
    message?: string
    confirmText?: string
    cancelText?: string
  }>(),
  {
    open: false,
    title: "确认操作",
    message: "请确认是否继续该操作。",
    confirmText: "确认",
    cancelText: "取消",
  }
)

const emit = defineEmits<{
  (event: "confirm"): void
  (event: "cancel"): void
}>()

const handleCancel = () => {
  emit("cancel")
}

const handleConfirm = () => {
  emit("confirm")
}
</script>

<template>
  <dialog class="modal" :open="props.open">
    <div class="modal-box">
      <h3 class="text-lg font-bold">{{ props.title }}</h3>
      <div class="mt-3 text-sm">
        <slot>{{ props.message }}</slot>
      </div>
      <div class="modal-action">
        <button class="btn" @click="handleCancel">{{ props.cancelText }}</button>
        <button class="btn btn-primary" @click="handleConfirm">
          {{ props.confirmText }}
        </button>
      </div>
    </div>
  </dialog>
</template>
