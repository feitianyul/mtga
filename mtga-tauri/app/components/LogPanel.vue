<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    logs?: string[]
    emptyText?: string
  }>(),
  {
    logs: () => [],
    emptyText: "日志输出占位",
  }
)

const logBox = ref<HTMLDivElement | null>(null)

const formattedLogs = computed(() =>
  props.logs && props.logs.length ? props.logs.join("\n") : props.emptyText
)

watch(
  () => props.logs,
  async () => {
    await nextTick()
    if (logBox.value) {
      logBox.value.scrollTop = logBox.value.scrollHeight
    }
  },
  { deep: true }
)
</script>

<template>
  <div class="card bg-base-200 shadow-sm">
    <div class="card-body p-4">
      <h2 class="card-title text-base">日志</h2>
      <div
        ref="logBox"
        class="mt-2 h-80 overflow-auto rounded bg-base-100 p-3 text-sm font-mono text-base-content/80"
      >
        <pre class="whitespace-pre-wrap leading-relaxed">{{ formattedLogs }}</pre>
      </div>
    </div>
  </div>
</template>
