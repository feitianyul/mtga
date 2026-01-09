<script setup lang="ts">
const {
  logs,
  init,
  updateDialogOpen,
  updateVersionLabel,
  updateNotesHtml,
  updateReleaseUrl,
  runCheckUpdatesOnce,
  closeUpdateDialog,
  openUpdateRelease,
} = useMtgaStore()

onMounted(async () => {
  await init()
  await runCheckUpdatesOnce()
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

  <UpdateDialog
    :open="updateDialogOpen"
    :version-label="updateVersionLabel"
    :notes-html="updateNotesHtml"
    :release-url="updateReleaseUrl"
    @close="closeUpdateDialog"
    @open-release="openUpdateRelease"
  />
</template>
