<script setup lang="ts">
const { logs, init } = useMtgaStore()

onMounted(async () => {
  await init()
})
</script>

<template>
  <AppShell>
    <template #left>
      <ConfigGroupPanel />
      <GlobalConfigPanel />
      <RuntimeOptionsPanel />
      <MainTabs />
    </template>

    <template #right>
      <LogPanel :logs="logs" />
    </template>

    <template #footer>
      <FooterActions />
    </template>
  </AppShell>
</template>
