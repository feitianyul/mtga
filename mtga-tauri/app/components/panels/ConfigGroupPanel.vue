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

const testTooltip = [
  "测试选中配置组的实际对话功能",
  "会发送最小请求并消耗少量tokens",
  "请确保配置正确后使用",
].join("\n")

const refreshTooltip = [
  "重新加载配置文件中的配置组",
  "用于同步外部修改或恢复意外更改",
].join("\n")

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

/**
 * 获取 API Key 的显示文本
 * 规则：
 * 1. 长度 <= 12 位时，全部显示为星号
 * 2. 长度 > 12 位时，每超出一位显示一位明文，上限为 4 位明文
 * 3. 显示的总长度（星号+明文）与实际长度一致
 */
const getApiKeyDisplay = (group: ConfigGroup) => {
  if ("target_model_id" in group) {
    return group.target_model_id || "(无)"
  }
  const apiKey = group.api_key || ""
  if (!apiKey) {
    return "(无)"
  }

  const len = apiKey.length
  const threshold = 12
  const maxVisible = 4

  // 计算可见字符数：超出阈值的部分，且不超过上限
  const visibleCount = Math.min(Math.max(0, len - threshold), maxVisible)

  if (visibleCount > 0) {
    return `${"*".repeat(len - visibleCount)}${apiKey.slice(-visibleCount)}`
  }
  return "*".repeat(len)
}

const refreshList = async () => {
  const ok = await store.loadConfig()
  if (ok) {
    store.appendLog("已刷新配置组列表")
  }
}

const requestTest = async () => {
  if (!hasSelection.value) {
    store.appendLog("请先选择要测活的配置组")
    return
  }
  await store.runConfigGroupTest(selectedIndex.value)
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
  <div class="mtga-card">
    <div class="mtga-card-body">
      <div class="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 class="mtga-card-title">代理服务器配置组</h2>
          <p class="mtga-card-subtitle">管理模型路由与鉴权组合</p>
        </div>
        <div class="flex items-center gap-2">
          <button
            class="btn btn-sm btn-outline rounded-xl border-slate-200 hover:border-amber-500 hover:bg-amber-50/50 hover:text-amber-600 tooltip mtga-tooltip"
            :data-tip="testTooltip"
            style="--mtga-tooltip-max: 250px;"
            @click="requestTest"
          >
            测活
          </button>
          <button
            class="btn btn-sm btn-outline rounded-xl border-slate-200 hover:border-amber-500 hover:bg-amber-50/50 hover:text-amber-600 tooltip mtga-tooltip"
            :data-tip="refreshTooltip"
            style="--mtga-tooltip-max: 250px;"
            @click="refreshList"
          >
            刷新
          </button>
        </div>
      </div>

      <div class="mt-4 grid gap-4 lg:grid-cols-[1fr,180px]">
        <div 
          class="min-w-0 rounded-xl border border-slate-200/70 bg-white/80 overflow-hidden flex flex-col" 
          style="--row-h: 36px; --head-h: 38px;"
        >
          <div class="overflow-auto custom-scrollbar flex-1 max-h-[182px]">
            <table class="table table-sm w-full text-sm border-separate border-spacing-0">
              <thead class="sticky top-0 z-10 bg-slate-50/90 backdrop-blur-sm">
                <tr style="height: var(--head-h)">
                  <th class="w-16 text-center border-b border-slate-200/60">序号</th>
                  <th class="min-w-[140px] border-b border-slate-200/60">API URL</th>
                  <th class="min-w-[120px] border-b border-slate-200/60">实际模型ID</th>
                  <th class="min-w-[160px] border-b border-slate-200/60">API Key</th>
                </tr>
              </thead>
              <tbody v-if="configGroups.length">
                <tr
                  v-for="(group, index) in configGroups"
                  :key="index"
                  class="cursor-pointer transition-colors hover:bg-slate-50"
                  :class="selectedIndex === index ? 'bg-amber-50/80' : ''"
                  :style="{ height: 'var(--row-h)' }"
                  :title="group.name || ''"
                  @click="selectedIndex = index"
                >
                  <td
                    class="w-16 border-l-4 text-center"
                    :class="
                      selectedIndex === index
                        ? 'border-amber-400 text-slate-900'
                        : 'border-transparent text-slate-600'
                    "
                  >
                    {{ index + 1 }}
                  </td>
                  <td class="truncate max-w-[200px] text-slate-700">
                    {{ group.api_url || "(未填写)" }}
                  </td>
                  <td class="truncate max-w-[150px] text-slate-700">
                    {{ group.model_id || "(未填写)" }}
                  </td>
                  <td class="truncate max-w-[200px] text-slate-700">{{ getApiKeyDisplay(group) }}</td>
                </tr>
              </tbody>
              <tbody v-else>
                <tr>
                  <td colspan="4" class="py-6 text-center text-sm text-slate-400">
                    暂无配置组
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="space-y-2">
          <button class="btn btn-primary btn-sm w-full rounded-xl shadow-sm" @click="openAdd">新增</button>
          <button class="btn btn-outline btn-sm w-full rounded-xl border-slate-200 hover:border-amber-500 hover:bg-amber-50/50 hover:text-amber-600" @click="openEdit">修改</button>
          <button class="btn btn-outline btn-sm w-full rounded-xl border-slate-200 text-error hover:bg-error/10 hover:border-error" @click="requestDelete">
            删除
          </button>
          <div class="h-px bg-slate-200/70 mx-1"></div>
          <button class="btn btn-outline btn-sm w-full rounded-xl border-slate-200 hover:border-slate-300 hover:bg-slate-50" @click="moveUp">上移</button>
          <button class="btn btn-outline btn-sm w-full rounded-xl border-slate-200 hover:border-slate-300 hover:bg-slate-50" @click="moveDown">下移</button>
        </div>
      </div>
    </div>
  </div>

  <dialog class="modal" :open="editorOpen">
    <div class="modal-box mtga-card">
      <div class="mtga-card-body">
        <div class="flex items-center justify-between gap-3">
          <div>
            <h3 class="text-lg font-semibold text-slate-900">
              {{ editorMode === "add" ? "新增配置组" : "修改配置组" }}
            </h3>
            <p class="text-xs text-slate-500">配置代理目标与鉴权参数</p>
          </div>
          <span class="mtga-chip">配置编辑</span>
        </div>
      </div>
      <div class="mt-2 px-5 pb-5">
        <label class="form-control">
          <div class="label pb-1">
            <span class="label-text text-xs text-slate-500">配置组名称（可选）</span>
          </div>
          <input v-model="form.name" class="input input-bordered w-full bg-white/80" />
        </label>
        <label class="form-control">
          <div class="label pb-1">
            <span class="label-text text-xs text-slate-500">* API URL</span>
          </div>
          <input v-model="form.api_url" class="input input-bordered w-full bg-white/80" />
        </label>
        <div class="flex items-center gap-3 pt-2">
          <label class="flex shrink-0 cursor-pointer items-center gap-2 whitespace-nowrap">
            <input
              v-model="middleRouteEnabled"
              type="checkbox"
              class="checkbox checkbox-sm"
            />
            <span class="label-text text-xs text-slate-500">修改中间路由</span>
          </label>
          <input
            v-model="form.middle_route"
            class="input input-bordered w-full bg-white/80"
            :disabled="!middleRouteEnabled"
            :placeholder="DEFAULT_MIDDLE_ROUTE"
          />
        </div>
        <label class="form-control">
          <div class="label pb-1">
            <span class="label-text text-xs text-slate-500">* 实际模型ID</span>
          </div>
          <input v-model="form.model_id" class="input input-bordered w-full bg-white/80" />
        </label>
        <label class="form-control">
          <div class="label pb-1">
            <span class="label-text text-xs text-slate-500">* API Key</span>
          </div>
          <input
            v-model="form.api_key"
            class="input input-bordered w-full bg-white/80"
            type="password"
          />
        </label>
        <p v-if="formError" class="text-sm text-error">{{ formError }}</p>      
        <p class="text-xs text-slate-400 pt-4">* 为必填项</p>
      </div>
      <div class="modal-action px-5 pb-5">
        <button class="btn btn-ghost rounded-xl" @click="closeEditor">取消</button>
        <button class="btn btn-primary rounded-xl px-8 shadow-sm" @click="handleSave">保存</button>
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
