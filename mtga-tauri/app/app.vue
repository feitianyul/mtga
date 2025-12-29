<script setup lang="ts">
const { showDataTab, logs, init, runGreet } = useMtgaStore()

onMounted(async () => {
  await init()
  await runGreet()
})
</script>

<template>
  <AppShell>
    <template #left>
      <ConfigGroupPanel />
      <GlobalConfigPanel />
      <RuntimeOptionsPanel />
      <MainTabs :show-data-tab="showDataTab" />
    </template>

    <template #right>
      <LogPanel :logs="logs" />
    </template>

    <template #footer>
      <FooterActions />
    </template>
  </AppShell>
</template>
