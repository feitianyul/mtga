<script setup lang="ts">
const store = useMtgaStore()
const options = store.runtimeOptions

const debugModeTooltip = [
  "开启后：",
  "1) 代理服务器输出更详细的调试日志，便于排查问题；",
  "2) 启动代理服务器前会额外检查系统/环境变量的显式代理配置",
  "并提示其可能绕过 hosts 导流。",
  "（默认不做第 2 项检查，仅在调试模式下启用）",
].join("\n")
</script>

<template>
  <div class="mtga-card">
    <div class="mtga-card-body">
      <div class="flex items-center justify-between gap-3">
        <div>
          <h2 class="mtga-card-title">运行时选项</h2>
          <p class="mtga-card-subtitle">控制代理运行行为与调试细节</p>
        </div>
        <span class="mtga-chip">运行模式</span>
      </div>
      <div class="mt-4 space-y-3">
        <div class="mtga-soft-panel space-y-3">
          <label
            class="flex items-center gap-3 text-sm text-slate-700 tooltip mtga-tooltip"
            :data-tip="debugModeTooltip"
            style="--mtga-tooltip-max: 500px;"
          >
            <input v-model="options.debugMode" type="checkbox" class="checkbox checkbox-sm" />
            <span>开启调试模式</span>
          </label>
          <label class="flex items-center gap-3 text-sm text-slate-700">
            <input
              v-model="options.disableSslStrict"
              type="checkbox"
              class="checkbox checkbox-sm"
            />
            <span>关闭SSL严格模式</span>
          </label>
          <div class="flex flex-wrap items-center gap-3 text-sm text-slate-700">
            <label class="flex items-center gap-3">
              <input
                v-model="options.forceStream"
                type="checkbox"
                class="checkbox checkbox-sm"
              />
              <span>强制流模式</span>
            </label>
            <select
              v-model="options.streamMode"
              class="select select-bordered select-sm bg-white/80"
              :disabled="!options.forceStream"
            >
              <option value="true">true</option>
              <option value="false">false</option>
            </select>
          </div>
        </div>
        <p class="text-xs text-slate-500">
          调试模式会输出更详细的日志，建议在排查问题时启用。
        </p>
      </div>
    </div>
  </div>
</template>
