import { useMtgaApi } from "./useMtgaApi"
import { isTauriRuntime } from "./runtime"
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
  user_data_dir: "",
  default_user_data_dir: "",
}

const DEFAULT_RUNTIME_OPTIONS: RuntimeOptions = {
  debugMode: false,
  disableSslStrict: false,
  forceStream: false,
  streamMode: "true",
}

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value)

const coerceText = (value: unknown) => {
  if (typeof value === "string") {
    return value
  }
  if (typeof value === "number") {
    return String(value)
  }
  if (isRecord(value)) {
    const candidates = [value["id"], value["value"], value["model_id"]]
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
  const logCursor = useState<number>("mtga-log-cursor", () => 0)
  const logStreamActive = useState<boolean>("mtga-log-stream-active", () => false)
  const appInfo = useState<AppInfo>("mtga-app-info", () => ({ ...DEFAULT_APP_INFO }))
  const initialized = useState<boolean>("mtga-initialized", () => false)
  const updateDialogOpen = useState<boolean>("mtga-update-dialog-open", () => false)
  const updateVersionLabel = useState<string>("mtga-update-version-label", () => "")
  const updateNotesHtml = useState<string>("mtga-update-notes-html", () => "")
  const updateReleaseUrl = useState<string>("mtga-update-release-url", () => "")
  const updateAutoChecked = useState<boolean>(
    "mtga-update-auto-checked",
    () => false
  )

  const appendLog = (message: string) => {
    logs.value.push(message)
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
    if (result.message) {
      appendLog(result.message)
    }
    return result.ok
  }

  const startLogStream = () => {
    if (logStreamActive.value) {
      return
    }
    logStreamActive.value = true

    const loop = async () => {
      if (!logStreamActive.value) {
        return
      }
      const result = await api.pullLogs({
        after_id: logCursor.value || null,
        timeout_ms: 0,
        max_items: 200,
      })
      if (!logStreamActive.value) {
        return
      }
      if (result) {
        if (Array.isArray(result.items) && result.items.length) {
          appendLogs(result.items)
        }
        if (typeof result.next_id === "number") {
          logCursor.value = result.next_id
        }
      }
      setTimeout(loop, 200)
    }

    void loop()
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

  const buildStartupLogs = (details: Record<string, unknown>) => {
    const envOk = details["env_ok"] === true
    const envMessage = coerceText(details["env_message"])
    if (envMessage) {
      appendLog(`${envOk ? "✅" : "❌"} ${envMessage}`)
    }
    if (envOk) {
      const runtime = coerceText(details["runtime"])
      if (runtime === "tauri" || runtime === "nuitka") {
        appendLog("📦 运行在打包环境中")
      } else {
        appendLog("🔧 运行在开发环境中")
      }
    }

    const allowFlag =
      coerceText(details["allow_unsafe_hosts_flag"]) || "--allow-unsafe-hosts"
    const hostsModifyBlocked = details["hosts_modify_blocked"] === true
    if (hostsModifyBlocked) {
      const status = coerceText(details["hosts_modify_block_status"]) || "unknown"
      appendLog(
        `⚠️ 检测到 hosts 文件写入受限（status=${status}），已启用受限 hosts 模式：添加将回退为追加写入（无法保证原子性增删/去重），自动移除/还原将被禁用。`
      )
      appendLog(
        `⚠️ 你可以点击「打开hosts文件」手动修改；或使用启动参数 ${allowFlag} 覆盖此检查以强制尝试原子写入（风险自负）。`
      )
    } else {
      const preflightOk = details["hosts_preflight_ok"] === true
      const preflightStatus = coerceText(details["hosts_preflight_status"])
      if (preflightStatus && !preflightOk) {
        appendLog(
          `⚠️ hosts 预检未通过（status=${preflightStatus}），但已使用启动参数 ${allowFlag} 覆盖；后续自动修改可能失败。`
        )
      }
    }

    if (details["explicit_proxy_detected"] === true) {
      appendLog(
        "⚠️".repeat(21) +
          "\n检测到显式代理配置：部分应用可能优先走代理，从而绕过 hosts 导流。"
      )
      appendLog("建议：1. 关闭显式代理（如clash的系统代理），或改用 TUN/VPN")
      appendLog("      2. 检查 Trae 的代理设置。\n" + "⚠️".repeat(21))
    }

    appendLog("MTGA GUI 已启动")
    appendLog("请选择操作或直接使用一键启动...")
  }

  const loadStartupStatus = async () => {
    const result = await api.getStartupStatus()
    if (!result) {
      appendLog("启动日志加载失败：无法连接后端")
      return false
    }
    if (isRecord(result.details)) {
      buildStartupLogs(result.details)
    }
    return result.ok
  }

  const init = async () => {
    if (initialized.value) {
      return
    }
    initialized.value = true
    startLogStream()
    await Promise.all([loadAppInfo(), loadConfig(), loadStartupStatus()])
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
    const ok = applyInvokeResult(result, "检查更新")
    if (!result || !isRecord(result.details)) {
      return ok
    }
    const updateResult = isRecord(result.details["update_result"])
      ? result.details["update_result"]
      : result.details
    const status = coerceText(updateResult["status"])
    if (status === "new_version") {
      updateVersionLabel.value = coerceText(updateResult["latest_version"])
      updateNotesHtml.value = coerceText(updateResult["release_notes"])
      updateReleaseUrl.value = coerceText(updateResult["release_url"])
      updateDialogOpen.value = true
    } else if (status === "up_to_date") {
      const latestVersion = coerceText(updateResult["latest_version"])
      if (latestVersion) {
        appendLog(`已是最新版本：${latestVersion}`)
      }
    }
    return ok
  }

  const runCheckUpdatesOnce = async () => {
    if (updateAutoChecked.value) {
      return false
    }
    updateAutoChecked.value = true
    return runCheckUpdates()
  }

  const closeUpdateDialog = () => {
    updateDialogOpen.value = false
  }

  const openUpdateRelease = async () => {
    const url = updateReleaseUrl.value.trim()
    if (!url || typeof window === "undefined") {
      return
    }
    if (isTauriRuntime()) {
      try {
        const { open } = await import("@tauri-apps/plugin-shell")
        await open(url)
        return
      } catch (error) {
        console.warn("[mtga] open release url failed", error)
        appendLog("打开发布页失败，请手动复制链接")
        return
      }
    }
    const opened = window.open(url, "_blank", "noopener,noreferrer")
    if (!opened) {
      window.location.href = url
    }
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
    logCursor,
    appInfo,
    updateDialogOpen,
    updateVersionLabel,
    updateNotesHtml,
    updateReleaseUrl,
    appendLog,
    startLogStream,
    loadConfig,
    saveConfig,
    init,
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
    runCheckUpdatesOnce,
    closeUpdateDialog,
    openUpdateRelease,
    runPlaceholder,
  }
}
