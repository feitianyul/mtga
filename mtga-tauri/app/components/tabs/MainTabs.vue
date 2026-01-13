<script setup lang="ts">

type TabKey = "cert" | "hosts" | "proxy" | "data";
const tabs: { key: TabKey; label: string }[] = [
  { key: "cert", label: "证书管理" },
  { key: "hosts", label: "hosts文件管理" },
  { key: "proxy", label: "代理服务器操作" },
  { key: "data", label: "用户数据管理" },
];

const activeTab = ref<TabKey>("cert");

const selectTab = (key: TabKey) => {
  activeTab.value = key;
};
</script>

<template>
  <div class="flex flex-wrap items-center justify-between gap-3">
    <div>
      <h2 class="mtga-card-title">功能操作</h2>
      <p class="mtga-card-subtitle">证书 / hosts / 代理 / 数据</p>
    </div>
    <span class="mtga-chip">工具集</span>
  </div>
  <div role="tablist" class="mt-4 flex flex-wrap gap-3 border-b border-slate-200/70 pb-2">
    <button
      v-for="tab in tabs"
      :key="tab.key"
      role="tab"
      type="button"
      class="cursor-pointer px-3 py-2 text-sm font-medium text-slate-500 transition-colors duration-150"
      :class="activeTab === tab.key ? 'border-b-2 border-amber-500 text-slate-900' : 'border-b-2 border-transparent hover:text-slate-800'"
      :aria-selected="activeTab === tab.key"
      @click="selectTab(tab.key)"
    >
      {{ tab.label }}
    </button>
  </div>

  <div class="mt-4 space-y-4">
    <section v-show="activeTab === 'cert'">
      <CertTab />
    </section>
    <section v-show="activeTab === 'hosts'">
      <HostsTab />
    </section>
    <section v-show="activeTab === 'proxy'">
      <ProxyTab />
    </section>
    <section v-show="activeTab === 'data'">
      <DataManagementTab />
    </section>
  </div>
</template>
