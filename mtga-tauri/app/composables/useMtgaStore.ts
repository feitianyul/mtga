import { useMtgaApi } from "./useMtgaApi"
import type { AppInfo, ConfigGroup, ConfigPayload, InvokeResult } from "./mtgaTypes"

type RuntimeOptions = {
  debugMode: boolean
  disableSslStrict: boolean
  forceStream: boolean
  streamMode: "true" | "false"
}

const DEFAULT_APP_INFO: AppInfo = {
  display_name: "MTGA",
  version: "v0.0.0",
  github_repo: "",
  ca_common_name: "MTGA_CA",
  api_key_visible_chars: 4,
}

const DEFAULT_RUNTIME_OPTIONS: RuntimeOptions = {
  debugMode: false,
  disableSslStrict: false,
  forceStream: false,
  streamMode: "true",
}

const clampIndex = (value: number, max: number) => {
  if (max <= 0) {
    return 0
  }
  return Math.min(Math.max(value, 0), max - 1)
}

export const useMtgaStore = () => {
  const api = useMtgaApi()

  const configGroups = useState<ConfigGroup[]>("mtga-config-groups", () => [])
  const currentConfigIndex = useState<number>("mtga-current-config-index", () => 0)
  const mappedModelId = useState<string>("mtga-mapped-model-id", () => "")
  const mtgaAuthKey = useState<string>("mtga-auth-key", () => "")
  const runtimeOptions = useState<RuntimeOptions>(
    "mtga-runtime-options",
    () => ({ ...DEFAULT_RUNTIME_OPTIONS })
  )
  const logs = useState<string[]>("mtga-logs", () => [])
  const appInfo = useState<AppInfo>("mtga-app-info", () => ({ ...DEFAULT_APP_INFO }))
  const showDataTab = useState<boolean>("mtga-show-data-tab", () => true)
  const initialized = useState<boolean>("mtga-initialized", () => false)

  const appendLog = (message: string) => {
    const stamp = new Date().toLocaleTimeString()
    logs.value.push(`[${stamp}] ${message}`)
  }

  const appendLogs = (entries?: string[]) => {
    if (!entries || !entries.length) {
      return
    }
    entries.forEach((entry) => appendLog(entry))
  }

  const applyInvokeResult = (
    result: InvokeResult | null,
    fallbackMessage: string
  ) => {
    if (!result) {
      appendLog(`${fallbackMessage}失败：无法连接后端`)
      return false
    }
    appendLogs(result.logs)
    if (result.message) {
      appendLog(result.message)
    }
    return result.ok
  }

  const loadConfig = async () => {
    const result = await api.loadConfig()
    if (!result) {
      return false
    }
    configGroups.value = result.config_groups || []
    currentConfigIndex.value = clampIndex(
      result.current_config_index ?? 0,
      configGroups.value.length
    )
    mappedModelId.value = result.mapped_model_id || ""
    mtgaAuthKey.value = result.mtga_auth_key || ""
    return true
  }

  const saveConfig = async () => {
    const clampedIndex = clampIndex(
      currentConfigIndex.value,
      configGroups.value.length
    )
    currentConfigIndex.value = clampedIndex
    const payload: ConfigPayload = {
      config_groups: configGroups.value,
      current_config_index: clampedIndex,
      mapped_model_id: mappedModelId.value,
      mtga_auth_key: mtgaAuthKey.value,
    }
    const ok = await api.saveConfig(payload)
    return Boolean(ok)
  }

  const loadAppInfo = async () => {
    const info = await api.getAppInfo()
    if (!info) {
      return false
    }
    appInfo.value = {
      ...DEFAULT_APP_INFO,
      ...info,
    }
    return true
  }

  const loadPackagedState = async () => {
    const packaged = await api.getIsPackaged()
    if (typeof packaged === "boolean") {
      showDataTab.value = packaged
    }
    return packaged
  }

  const init = async () => {
    if (initialized.value) {
      return
    }
    initialized.value = true
    await Promise.all([loadAppInfo(), loadConfig(), loadPackagedState()])
  }

  const runGreet = async () => {
    const response = await api.greet("bifang")
    if (response) {
      appendLog(response)
    }
  }

  const runHostsModify = async (
    mode: "add" | "backup" | "restore" | "remove"
  ) => {
    const result = await api.hostsModify({ mode })
    return applyInvokeResult(result, "hosts 操作")
  }

  const runHostsOpen = async () => {
    const result = await api.hostsOpen()
    return applyInvokeResult(result, "打开 hosts 文件")
  }

  const runPlaceholder = (label: string) => {
    appendLog(`${label}（待接入后端）`)
  }

  return {
    configGroups,
    currentConfigIndex,
    mappedModelId,
    mtgaAuthKey,
    runtimeOptions,
    logs,
    appInfo,
    showDataTab,
    appendLog,
    loadConfig,
    saveConfig,
    init,
    runGreet,
    runHostsModify,
    runHostsOpen,
    runPlaceholder,
  }
}
