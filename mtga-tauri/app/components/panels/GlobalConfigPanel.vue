<script setup lang="ts">
const store = useMtgaStore()
const saving = ref(false)
const mappedModelId = computed({
  get: () => store.mappedModelId.value,
  set: (value) => {
    store.mappedModelId.value = value
  },
})
const mtgaAuthKey = computed({
  get: () => store.mtgaAuthKey.value,
  set: (value) => {
    store.mtgaAuthKey.value = value
  },
})

const handleSave = async () => {
  if (!store.mappedModelId.value || !store.mtgaAuthKey.value) {
    store.appendLog("错误: 映射模型ID和MTGA鉴权Key都是必填项")
    return
  }
  saving.value = true
  const ok = await store.saveConfig()
  saving.value = false
  if (ok) {
    store.appendLog("全局配置已保存")
  } else {
    store.appendLog("保存全局配置失败")
  }
}
</script>

<template>
  <div class="mtga-card">
    <div class="mtga-card-body">
      <div class="flex items-center justify-between gap-3">
        <div>
          <h2 class="mtga-card-title">全局配置</h2>
          <p class="mtga-card-subtitle">管理映射模型与鉴权信息</p>
        </div>
        <span class="mtga-chip">全局参数</span>
      </div>
      <div class="mt-4 space-y-4">
        <div class="mtga-soft-panel space-y-3">
          <label class="form-control">
            <div class="label pb-1">
              <span class="label-text text-xs text-slate-500">映射模型ID</span>
            </div>
            <input
              v-model="mappedModelId"
              class="input input-bordered w-full bg-white/80"
              placeholder="例如：gpt-5"
            />
          </label>

          <label class="form-control">
            <div class="label pb-1">
              <span class="label-text text-xs text-slate-500">MTGA鉴权Key</span>
            </div>
            <input
              v-model="mtgaAuthKey"
              class="input input-bordered w-full bg-white/80"
              placeholder="例如：111"
              type="password"
            />
          </label>
        </div>

        <div class="flex items-center justify-between gap-3">
          <span class="text-xs text-slate-500">保存后会同步所有配置组</span>
          <button
            class="btn btn-primary btn-sm px-4 shadow-[0_12px_24px_-18px_rgba(14,165,164,0.8)]"
            :disabled="saving"
            @click="handleSave"
          >
            保存全局配置
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
