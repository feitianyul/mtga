<template>
  <AppShell>
    <template #left>
      <ConfigGroupPanel />
      <GlobalConfigPanel />
      <RuntimeOptionsPanel />
      <MainTabs>
        <CertTab />
      </MainTabs>
    </template>

    <template #right>
      <LogPanel />
    </template>

    <template #footer>
      <FooterActions />
    </template>
  </AppShell>
</template>
