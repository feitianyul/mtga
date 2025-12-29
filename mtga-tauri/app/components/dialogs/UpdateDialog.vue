<script setup lang="ts">
import DOMPurify from "dompurify"

const props = withDefaults(
  defineProps<{
    open?: boolean
    versionLabel?: string
    notesHtml?: string
    releaseUrl?: string
  }>(),
  {
    open: false,
    versionLabel: "",
    notesHtml: "",
    releaseUrl: "",
  }
)

const emit = defineEmits<{
  (event: "close"): void
  (event: "open-release"): void
}>()

const sanitizedNotesHtml = computed(() => {
  return DOMPurify.sanitize(props.notesHtml)
})

const handleClose = () => {
  emit("close")
}

const handleOpenRelease = () => {
  emit("open-release")
}
</script>

<template>
  <dialog class="modal" :open="props.open">
    <div class="modal-box">
      <h3 class="text-lg font-bold">
        发现新版本{{ props.versionLabel ? `：${props.versionLabel}` : "" }}
      </h3>
      <div class="mt-3 rounded bg-base-200 p-3 text-sm">
        <!-- eslint-disable-next-line vue/no-v-html -->
        <div v-if="sanitizedNotesHtml" v-html="sanitizedNotesHtml" />
        <div v-else>该版本暂无更新说明。</div>
      </div>
      <div class="modal-action">
        <button class="btn" @click="handleClose">关闭</button>
        <button class="btn btn-primary" :disabled="!props.releaseUrl" @click="handleOpenRelease">
          前往发布页
        </button>
      </div>
    </div>
  </dialog>
</template>
