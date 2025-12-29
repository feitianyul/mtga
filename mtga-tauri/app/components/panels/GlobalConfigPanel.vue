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
  <div class="card bg-base-200 shadow-sm">
    <div class="card-body p-4">
      <h2 class="card-title text-base">全局配置</h2>
      <div class="mt-3 space-y-3">
        <label class="form-control">
          <div class="label">
            <span class="label-text">映射模型ID</span>
          </div>
          <input
            v-model="mappedModelId"
            class="input input-bordered w-full"
            placeholder="例如：gpt-5"
          />
        </label>

        <label class="form-control">
          <div class="label">
            <span class="label-text">MTGA鉴权Key</span>
          </div>
          <input
            v-model="mtgaAuthKey"
            class="input input-bordered w-full"
            placeholder="例如：111"
            type="password"
          />
        </label>

        <div>
          <button class="btn btn-primary btn-sm" :disabled="saving" @click="handleSave">
            保存全局配置
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
