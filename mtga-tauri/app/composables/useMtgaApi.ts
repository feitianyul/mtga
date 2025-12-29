import { pyInvoke } from "tauri-plugin-pytauri-api"

import type { AppInfo, ConfigPayload } from "./mtgaTypes"

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
  const getIsPackaged = () => safeInvoke<boolean>("is_packaged", undefined, false)
  const greet = (name: string) => safeInvoke<string>("greet", { name }, "")

  return {
    loadConfig,
    saveConfig,
    getAppInfo,
    getIsPackaged,
    greet,
  }
}
