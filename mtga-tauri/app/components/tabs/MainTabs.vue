<script setup lang="ts">

type TabKey = "cert" | "hosts" | "proxy" | "data" | "about";
const tabs: { key: TabKey; label: string }[] = [
  { key: "cert", label: "证书管理" },
  { key: "hosts", label: "hosts文件管理" },
  { key: "proxy", label: "代理服务器操作" },
  { key: "data", label: "用户数据管理" },
  { key: "about", label: "关于" },
];

const activeTab = ref<TabKey>("cert");

const selectTab = (key: TabKey) => {
  activeTab.value = key;
};
</script>

<template>
  <div class="card bg-base-200 shadow-sm">
    <div class="card-body p-4">
      <div role="tablist" class="tabs tabs-bordered">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          role="tab"
          type="button"
          class="tab"
          :class="{ 'tab-active': activeTab === tab.key }"
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
        <section v-show="activeTab === 'about'">
          <AboutTab />
        </section>
      </div>
    </div>
  </div>
</template>
