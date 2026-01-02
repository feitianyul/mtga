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

const coerceText = (value: unknown) => {
  if (typeof value === "string") {
    return value
  }
  if (typeof value === "number") {
    return String(value)
  }
  if (value && typeof value === "object") {
    const record = value as Record<string, unknown>
    const candidates = [record["id"], record["value"], record["model_id"]]
    for (const candidate of candidates) {
      if (typeof candidate === "string") {
        return candidate
      }
    }
  }
  return ""
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
    mappedModelId.value = coerceText(result.mapped_model_id)
    mtgaAuthKey.value = coerceText(result.mtga_auth_key)
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
      mapped_model_id: coerceText(mappedModelId.value),
      mtga_auth_key: coerceText(mtgaAuthKey.value),
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

  const init = async () => {
    if (initialized.value) {
      return
    }
    initialized.value = true
    await Promise.all([loadAppInfo(), loadConfig()])
  }

  const runGreet = async () => {
    const response = await api.greet("bifang")
    if (response) {
      appendLog(response)
    }
  }

  const buildProxyPayload = () => ({
    debug_mode: runtimeOptions.value.debugMode,
    disable_ssl_strict_mode: runtimeOptions.value.disableSslStrict,
    force_stream: runtimeOptions.value.forceStream,
    stream_mode: runtimeOptions.value.streamMode,
  })

  const runGenerateCertificates = async () => {
    const result = await api.generateCertificates()
    return applyInvokeResult(result, "生成证书")
  }

  const runInstallCaCert = async () => {
    const result = await api.installCaCert()
    return applyInvokeResult(result, "安装 CA 证书")
  }

  const runClearCaCert = async () => {
    const result = await api.clearCaCert()
    return applyInvokeResult(result, "清除 CA 证书")
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

  const runProxyStart = async () => {
    const result = await api.proxyStart(buildProxyPayload())
    return applyInvokeResult(result, "启动代理服务器")
  }

  const runProxyStop = async () => {
    const result = await api.proxyStop()
    return applyInvokeResult(result, "停止代理服务器")
  }

  const runProxyCheckNetwork = async () => {
    const result = await api.proxyCheckNetwork()
    return applyInvokeResult(result, "检查网络环境")
  }

  const runProxyStartAll = async () => {
    const result = await api.proxyStartAll(buildProxyPayload())
    return applyInvokeResult(result, "一键启动全部服务")
  }

  const runConfigGroupTest = async (index: number) => {
    const result = await api.configGroupTest({ index })
    return applyInvokeResult(result, "配置组测活")
  }

  const runUserDataOpenDir = async () => {
    const result = await api.userDataOpenDir()
    return applyInvokeResult(result, "打开用户数据目录")
  }

  const runUserDataBackup = async () => {
    const result = await api.userDataBackup()
    return applyInvokeResult(result, "备份用户数据")
  }

  const runUserDataRestoreLatest = async () => {
    const result = await api.userDataRestoreLatest()
    return applyInvokeResult(result, "还原用户数据")
  }

  const runUserDataClear = async () => {
    const result = await api.userDataClear()
    return applyInvokeResult(result, "清除用户数据")
  }

  const runCheckUpdates = async () => {
    const result = await api.checkUpdates()
    return applyInvokeResult(result, "检查更新")
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
    appendLog,
    loadConfig,
    saveConfig,
    init,
    runGreet,
    runGenerateCertificates,
    runInstallCaCert,
    runClearCaCert,
    runHostsModify,
    runHostsOpen,
    runProxyStart,
    runProxyStop,
    runProxyCheckNetwork,
    runProxyStartAll,
    runConfigGroupTest,
    runUserDataOpenDir,
    runUserDataBackup,
    runUserDataRestoreLatest,
    runUserDataClear,
    runCheckUpdates,
    runPlaceholder,
  }
}
