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

/**
 * 当前选中的左侧面板 ID
 */
const activeTab = ref('config-group')

/**
 * 导航菜单配置
 */
const navigation = [
  { id: 'config-group', name: '代理配置组', icon: 'M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4' },
  { id: 'global-config', name: '全局配置', icon: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z' },
  { id: 'runtime-options', name: '运行时选项', icon: 'M13 10V3L4 14h7v7l9-11h-7z' },
  { id: 'main-tabs', name: '功能操作页', icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z' },
]

onMounted(async () => {
  await init()
  await runCheckUpdatesOnce()
})
</script>

<template>
  <AppShell>
    <template #left>
      <div class="flex items-stretch bg-white/50 backdrop-blur-md rounded-3xl shadow-sm border border-slate-200/60 overflow-hidden h-full min-h-0">
        <!-- 垂直菜单栏 -->
        <div class="w-41 border-r border-slate-200/50 flex flex-col p-3 bg-slate-50/30 shrink-0">
          <ul class="menu p-0 gap-1">
            <li v-for="item in navigation" :key="item.id">
              <a 
                :class="[
                  'flex flex-row items-center justify-start gap-3 px-4 py-3 rounded-2xl transition-all duration-200 group border',
                  activeTab === item.id 
                    ? 'bg-amber-50/80 text-amber-600 border-amber-500/50 shadow-sm shadow-amber-500/10' 
                    : 'text-slate-500 border-transparent hover:bg-slate-200/50'
                ]"
                @click="activeTab = item.id"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 opacity-80 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="item.icon" />
                </svg>
                <span class="text-sm font-bold tracking-wide truncate">{{ item.name }}</span>
              </a>
            </li>
          </ul>
        </div>

        <!-- 面板内容区域 -->
        <div class="flex-1 min-w-0 p-6 overflow-hidden flex flex-col">
          <Transition
            enter-active-class="transition duration-200 ease-out"
            enter-from-class="translate-x-4 opacity-0"
            enter-to-class="translate-x-0 opacity-100"
            mode="out-in"
          >
            <div :key="activeTab" class="flex-1 overflow-y-auto overflow-x-hidden pr-2 custom-scrollbar">
              <ConfigGroupPanel v-if="activeTab === 'config-group'" />
              <GlobalConfigPanel v-if="activeTab === 'global-config'" />
              <RuntimeOptionsPanel v-if="activeTab === 'runtime-options'" />
              <MainTabs v-if="activeTab === 'main-tabs'" />
            </div>
          </Transition>
        </div>
      </div>
    </template>

    <template #right>
      <div class="h-full flex flex-col">
        <LogPanel :logs="logs" class="flex-1" />
      </div>
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
