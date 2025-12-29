export type ConfigGroup = {
  name?: string
  api_url: string
  model_id: string
  api_key: string
  middle_route?: string
  target_model_id?: string
  mapped_model_id?: string
}

export type ConfigPayload = {
  config_groups: ConfigGroup[]
  current_config_index: number
  mapped_model_id: string
  mtga_auth_key: string
}

export type AppInfo = {
  display_name: string
  version: string
  github_repo: string
  ca_common_name: string
  api_key_visible_chars: number
}

export type InvokeResult = {
  ok: boolean
  message?: string | null
  code?: string | null
  details?: Record<string, unknown>
  logs?: string[]
}
