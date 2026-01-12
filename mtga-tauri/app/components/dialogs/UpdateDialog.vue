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
  const source = props.notesHtml?.trim() ?? ""
  if (!source) {
    return ""
  }
  const sanitized = DOMPurify.sanitize(source, { WHOLE_DOCUMENT: true })
  if (!sanitized) {
    return ""
  }
  if (typeof window === "undefined") {
    return sanitized
  }
  try {
    const parser = new DOMParser()
    const doc = parser.parseFromString(sanitized, "text/html")
    doc.querySelectorAll("a[href]").forEach((anchor) => {
      anchor.setAttribute("target", "_blank")
      anchor.setAttribute("rel", "noopener noreferrer")
    })
    const bodyHtml = doc.body?.innerHTML?.trim() ?? ""
    return bodyHtml || sanitized
  } catch {
    return sanitized
  }
})

const isTauriRuntime = () =>
  typeof navigator !== "undefined" && /tauri/i.test(navigator.userAgent)

const resolveExternalUrl = (href: string) => {
  const trimmed = href.trim()
  if (!trimmed) {
    return ""
  }
  if (/^https?:\/\//i.test(trimmed)) {
    return trimmed
  }
  if (!props.releaseUrl) {
    return trimmed
  }
  try {
    return new URL(trimmed, props.releaseUrl).toString()
  } catch {
    return trimmed
  }
}

const openExternalUrl = async (href: string) => {
  const url = resolveExternalUrl(href)
  if (!url || typeof window === "undefined") {
    return
  }
  if (isTauriRuntime()) {
    try {
      const { open } = await import("@tauri-apps/plugin-shell")
      await open(url)
      return
    } catch (error) {
      console.warn("[mtga] open notes link failed", error)
      return
    }
  }
  const opened = window.open(url, "_blank", "noopener,noreferrer")
  if (!opened) {
    window.location.href = url
  }
}

const handleNotesClick = async (event: MouseEvent) => {
  const eventTarget = event.target
  if (!(eventTarget instanceof HTMLElement)) {
    return
  }
  const anchor = eventTarget.closest("a")
  if (!(anchor instanceof HTMLAnchorElement)) {
    return
  }
  const href = anchor.getAttribute("href") ?? ""
  if (!href) {
    return
  }
  event.preventDefault()
  await openExternalUrl(href)
}

const handleClose = () => {
  emit("close")
}

const handleOpenRelease = () => {
  emit("open-release")
}
</script>

<template>
  <dialog class="modal" :open="props.open">
    <div class="modal-box mtga-card">
      <div class="mtga-card-body">
        <h3 class="text-lg font-semibold text-slate-900">
          发现新版本{{ props.versionLabel ? `：${props.versionLabel}` : "" }}
        </h3>
        <div
          class="mt-3 rounded-xl border border-slate-200/70 bg-slate-50/80 p-3 text-sm text-slate-700"
          @click="handleNotesClick"
        >
          <!-- eslint-disable-next-line vue/no-v-html -->
          <div v-if="sanitizedNotesHtml" v-html="sanitizedNotesHtml" />
          <div v-else>该版本暂无更新说明。</div>
        </div>
      </div>
      <div class="modal-action px-5 pb-5">
        <button class="btn btn-ghost" @click="handleClose">关闭</button>
        <button class="btn btn-primary" :disabled="!props.releaseUrl" @click="handleOpenRelease">
          前往发布页
        </button>
      </div>
    </div>
  </dialog>
</template>
