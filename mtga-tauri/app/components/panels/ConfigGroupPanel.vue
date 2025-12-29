<script setup lang="ts">
import type { ConfigGroup } from "~/composables/mtgaTypes"

const store = useMtgaStore()
const configGroups = store.configGroups
const currentIndex = store.currentConfigIndex

const DEFAULT_MIDDLE_ROUTE = "/v1"

const editorOpen = ref(false)
const editorMode = ref<"add" | "edit">("add")
const formError = ref("")
const middleRouteEnabled = ref(false)

const confirmOpen = ref(false)
const confirmTitle = ref("确认删除")
const confirmMessage = ref("")
const pendingDeleteIndex = ref<number | null>(null)

const form = reactive({
  name: "",
  api_url: "",
  model_id: "",
  api_key: "",
  middle_route: "",
})

const selectedIndex = computed({
  get: () => (configGroups.value.length ? currentIndex.value : -1),
  set: (value) => {
    if (value < 0 || value >= configGroups.value.length) {
      return
    }
    currentIndex.value = value
    void store.saveConfig()
  },
})

const hasSelection = computed(
  () =>
    configGroups.value.length > 0 &&
    selectedIndex.value >= 0 &&
    selectedIndex.value < configGroups.value.length
)

const apiKeyVisibleChars = computed(
  () => store.appInfo.value.api_key_visible_chars || 4
)

const normalizeMiddleRoute = (value: string) => {
  let raw = value.trim()
  if (!raw) {
    raw = DEFAULT_MIDDLE_ROUTE
  }
  if (!raw.startsWith("/")) {
    raw = `/${raw}`
  }
  if (raw.length > 1) {
    raw = raw.replace(/\/+$/, "")
    if (!raw) {
      raw = "/"
    }
  }
  return raw
}

const getDisplayName = (group: ConfigGroup, index: number) =>
  group.name?.trim() || `配置组 ${index + 1}`

const getApiKeyDisplay = (group: ConfigGroup) => {
  if ("target_model_id" in group) {
    return group.target_model_id || "(无)"
  }
  const apiKey = group.api_key || ""
  if (!apiKey) {
    return "(无)"
  }
  const visible = apiKeyVisibleChars.value
  if (apiKey.length > visible) {
    return `${"*".repeat(apiKey.length - visible)}${apiKey.slice(-visible)}`
  }
  return "***"
}

const refreshList = async () => {
  const ok = await store.loadConfig()
  if (ok) {
    store.appendLog("已刷新配置组列表")
  }
}

const requestTest = () => {
  if (!hasSelection.value) {
    store.appendLog("请先选择要测活的配置组")
    return
  }
  store.runPlaceholder("配置组测活")
}

const resetForm = () => {
  form.name = ""
  form.api_url = ""
  form.model_id = ""
  form.api_key = ""
  form.middle_route = ""
  middleRouteEnabled.value = false
  formError.value = ""
}

const openAdd = () => {
  editorMode.value = "add"
  resetForm()
  editorOpen.value = true
}

const openEdit = () => {
  if (!hasSelection.value) {
    store.appendLog("请先选择要修改的配置组")
    return
  }
  editorMode.value = "edit"
  const group = configGroups.value[selectedIndex.value]
  if (!group) {
    return
  }
  form.name = group.name || ""
  form.api_url = group.api_url || ""
  form.model_id = group.model_id || ""
  form.api_key = group.api_key || ""
  form.middle_route = group.middle_route || ""
  middleRouteEnabled.value = Boolean(group.middle_route)
  formError.value = ""
  editorOpen.value = true
}

const closeEditor = () => {
  editorOpen.value = false
}

const handleSave = async () => {
  const payload: ConfigGroup = {
    name: form.name.trim(),
    api_url: form.api_url.trim(),
    model_id: form.model_id.trim(),
    api_key: form.api_key.trim(),
  }

  if (!payload.api_url || !payload.model_id || !payload.api_key) {
    formError.value = "API URL、实际模型ID 和 API Key 都是必填项"
    store.appendLog("错误: API URL、实际模型ID和API Key都是必填项")
    return
  }

  if (middleRouteEnabled.value && form.middle_route.trim()) {
    payload.middle_route = normalizeMiddleRoute(form.middle_route)
  }

  if (editorMode.value === "add") {
    configGroups.value.push(payload)
    currentIndex.value = configGroups.value.length - 1
  } else if (hasSelection.value) {
    configGroups.value.splice(selectedIndex.value, 1, payload)
  }

  const ok = await store.saveConfig()
  if (ok) {
    const displayName = getDisplayName(payload, selectedIndex.value)
    store.appendLog(
      editorMode.value === "add"
        ? `已添加配置组: ${displayName}`
        : `已修改配置组: ${displayName}`
    )
    closeEditor()
  } else {
    store.appendLog("保存配置组失败")
  }
}

const requestDelete = () => {
  if (!hasSelection.value) {
    store.appendLog("请先选择要删除的配置组")
    return
  }
  if (configGroups.value.length <= 1) {
    store.appendLog("至少需要保留一个配置组")
    return
  }
  const group = configGroups.value[selectedIndex.value]
  if (!group) {
    return
  }
  pendingDeleteIndex.value = selectedIndex.value
  confirmTitle.value = "确认删除"
  confirmMessage.value = `确定要删除配置组 “${getDisplayName(
    group,
    selectedIndex.value
  )}” 吗？`
  confirmOpen.value = true
}

const cancelDelete = () => {
  confirmOpen.value = false
  pendingDeleteIndex.value = null
}

const confirmDelete = async () => {
  if (pendingDeleteIndex.value == null) {
    return
  }
  const index = pendingDeleteIndex.value
  const group = configGroups.value[index]
  if (!group) {
    store.appendLog("配置组不存在，已取消删除")
    confirmOpen.value = false
    pendingDeleteIndex.value = null
    return
  }
  configGroups.value.splice(index, 1)
  if (currentIndex.value >= configGroups.value.length) {
    currentIndex.value = Math.max(configGroups.value.length - 1, 0)
  } else if (currentIndex.value > index) {
    currentIndex.value -= 1
  }
  const ok = await store.saveConfig()
  if (ok) {
    store.appendLog(`已删除配置组: ${getDisplayName(group, index)}`)
  } else {
    store.appendLog("保存配置组失败")
  }
  confirmOpen.value = false
  pendingDeleteIndex.value = null
}

const moveUp = async () => {
  if (!hasSelection.value || selectedIndex.value <= 0) {
    return
  }
  const index = selectedIndex.value
  const current = configGroups.value[index]
  const prev = configGroups.value[index - 1]
  if (!current || !prev) {
    return
  }
  configGroups.value[index - 1] = current
  configGroups.value[index] = prev
  currentIndex.value = index - 1
  await store.saveConfig()
}

const moveDown = async () => {
  if (
    !hasSelection.value ||
    selectedIndex.value >= configGroups.value.length - 1
  ) {
    return
  }
  const index = selectedIndex.value
  const current = configGroups.value[index]
  const next = configGroups.value[index + 1]
  if (!current || !next) {
    return
  }
  configGroups.value[index + 1] = current
  configGroups.value[index] = next
  currentIndex.value = index + 1
  await store.saveConfig()
}
</script>

<template>
  <div class="card bg-base-200 shadow-sm">
    <div class="card-body p-4">
      <div class="flex items-center justify-between">
        <h2 class="card-title text-base">代理服务器配置组</h2>
        <div class="flex gap-2">
          <button class="btn btn-sm" @click="requestTest">测活</button>
          <button class="btn btn-sm" @click="refreshList">刷新</button>
        </div>
      </div>

      <div class="mt-3 grid gap-4 lg:grid-cols-[1fr,160px]">
        <div class="overflow-auto rounded bg-base-100">
          <table class="table table-sm">
            <thead>
              <tr>
                <th>序号</th>
                <th>API URL</th>
                <th>实际模型ID</th>
                <th>API Key</th>
              </tr>
            </thead>
            <tbody v-if="configGroups.length">
              <tr
                v-for="(group, index) in configGroups"
                :key="index"
                class="cursor-pointer"
                :class="{ 'bg-base-300': selectedIndex === index }"
                :title="group.name || ''"
                @click="selectedIndex = index"
              >
                <td class="text-center">{{ index + 1 }}</td>
                <td class="truncate">
                  {{ group.api_url || "(未填写)" }}
                </td>
                <td class="truncate">{{ group.model_id || "(未填写)" }}</td>
                <td class="truncate">{{ getApiKeyDisplay(group) }}</td>
              </tr>
            </tbody>
            <tbody v-else>
              <tr>
                <td colspan="4" class="py-6 text-center text-sm text-base-content/60">
                  暂无配置组
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="space-y-2">
          <button class="btn btn-sm w-full" @click="openAdd">新增</button>
          <button class="btn btn-sm w-full" @click="openEdit">修改</button>
          <button class="btn btn-sm w-full" @click="requestDelete">删除</button>
          <button class="btn btn-sm w-full" @click="moveUp">上移</button>
          <button class="btn btn-sm w-full" @click="moveDown">下移</button>
        </div>
      </div>
    </div>
  </div>

  <dialog class="modal" :open="editorOpen">
    <div class="modal-box">
      <h3 class="text-lg font-bold">
        {{ editorMode === "add" ? "新增配置组" : "修改配置组" }}
      </h3>
      <div class="mt-4 space-y-3">
        <label class="form-control">
          <div class="label">
            <span class="label-text">配置组名称（可选）</span>
          </div>
          <input v-model="form.name" class="input input-bordered w-full" />
        </label>
        <label class="form-control">
          <div class="label">
            <span class="label-text">* API URL</span>
          </div>
          <input v-model="form.api_url" class="input input-bordered w-full" />
        </label>
        <label class="form-control">
          <div class="label">
            <span class="label-text">* 实际模型ID</span>
          </div>
          <input v-model="form.model_id" class="input input-bordered w-full" />
        </label>
        <label class="form-control">
          <div class="label">
            <span class="label-text">* API Key</span>
          </div>
          <input v-model="form.api_key" class="input input-bordered w-full" type="password" />
        </label>
        <div class="flex items-center gap-3">
          <label class="flex items-center gap-2">
            <input
              v-model="middleRouteEnabled"
              type="checkbox"
              class="checkbox checkbox-sm"
            />
            <span>修改中间路由</span>
          </label>
          <input
            v-model="form.middle_route"
            class="input input-bordered w-full"
            :disabled="!middleRouteEnabled"
            :placeholder="DEFAULT_MIDDLE_ROUTE"
          />
        </div>
        <p v-if="formError" class="text-sm text-error">{{ formError }}</p>
        <p class="text-xs text-base-content/60">* 为必填项</p>
      </div>
      <div class="modal-action">
        <button class="btn" @click="closeEditor">取消</button>
        <button class="btn btn-primary" @click="handleSave">保存</button>
      </div>
    </div>
  </dialog>

  <ConfirmDialog
    :open="confirmOpen"
    :title="confirmTitle"
    :message="confirmMessage"
    @cancel="cancelDelete"
    @confirm="confirmDelete"
  />
</template>
