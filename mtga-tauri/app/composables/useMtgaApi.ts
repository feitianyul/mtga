import { pyInvoke } from "tauri-plugin-pytauri-api"

import type { AppInfo, ConfigPayload, InvokeResult } from "./mtgaTypes"

type InvokePayload = Record<string, unknown>

const canInvoke = () => typeof window !== "undefined"

const safeInvoke = async <T>(
  command: string,
  payload?: InvokePayload,
  fallback?: T
): Promise<T | null> => {
  if (!canInvoke()) {
    return fallback ?? null
  }
  try {
    return await pyInvoke(command, payload)
  } catch (error) {
    console.warn(`[mtga] invoke ${command} failed`, error)
    return fallback ?? null
  }
}

export const useMtgaApi = () => {
  const loadConfig = () => safeInvoke<ConfigPayload>("load_config")
  const saveConfig = (payload: ConfigPayload) =>
    safeInvoke<boolean>("save_config", payload, false)
  const getAppInfo = () => safeInvoke<AppInfo>("get_app_info")
  const greet = (name: string) => safeInvoke<string>("greet", { name }, "")
  const hostsModify = (payload: {
    mode: "add" | "backup" | "restore" | "remove"
    domain?: string
    ip?: string[] | string
  }) => safeInvoke<InvokeResult>("hosts_modify", payload)
  const hostsOpen = () => safeInvoke<InvokeResult>("hosts_open")
  const generateCertificates = () =>
    safeInvoke<InvokeResult>("generate_certificates")
  const installCaCert = () => safeInvoke<InvokeResult>("install_ca_cert")
  const clearCaCert = () => safeInvoke<InvokeResult>("clear_ca_cert")
  const proxyStart = (payload: {
    debug_mode: boolean
    disable_ssl_strict_mode: boolean
    force_stream: boolean
    stream_mode?: string | null
  }) => safeInvoke<InvokeResult>("proxy_start", payload)
  const proxyStop = () => safeInvoke<InvokeResult>("proxy_stop")
  const proxyCheckNetwork = () =>
    safeInvoke<InvokeResult>("proxy_check_network")
  const proxyStartAll = (payload: {
    debug_mode: boolean
    disable_ssl_strict_mode: boolean
    force_stream: boolean
    stream_mode?: string | null
  }) => safeInvoke<InvokeResult>("proxy_start_all", payload)
  const configGroupTest = (payload: {
    index: number
    mode?: "chat" | "models"
  }) => safeInvoke<InvokeResult>("config_group_test", payload)
  const userDataOpenDir = () => safeInvoke<InvokeResult>("user_data_open_dir")
  const userDataBackup = () => safeInvoke<InvokeResult>("user_data_backup")
  const userDataRestoreLatest = () =>
    safeInvoke<InvokeResult>("user_data_restore_latest")
  const userDataClear = () => safeInvoke<InvokeResult>("user_data_clear")
  const checkUpdates = () => safeInvoke<InvokeResult>("check_updates")

  return {
    loadConfig,
    saveConfig,
    getAppInfo,
    greet,
    hostsModify,
    hostsOpen,
    generateCertificates,
    installCaCert,
    clearCaCert,
    proxyStart,
    proxyStop,
    proxyCheckNetwork,
    proxyStartAll,
    configGroupTest,
    userDataOpenDir,
    userDataBackup,
    userDataRestoreLatest,
    userDataClear,
    checkUpdates,
  }
}
