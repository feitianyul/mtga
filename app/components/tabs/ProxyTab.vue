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

const handleStart = () => {
  store.runProxyStart()
}

const handleStop = () => {
  store.runProxyStop()
}

const handleCheck = () => {
  store.runProxyCheckNetwork()
}
</script>

<template>
  <div class="mtga-soft-panel space-y-3 mb-4">
    <div>
      <div class="text-sm font-semibold text-slate-900">运行时选项</div>
      <div class="text-xs text-slate-500">控制代理运行行为与调试细节</div>
    </div>
    <div class="space-y-3">
      <label
        class="flex items-center gap-3 text-sm text-slate-700 tooltip mtga-tooltip cursor-pointer hover:bg-slate-100/50 rounded px-3 py-2 -my-1 transition-colors"
        :data-tip="debugModeTooltip"
        style="--mtga-tooltip-max: 500px;"
      >
        <input v-model="options.debugMode" type="checkbox" class="checkbox checkbox-sm" />
        <span>开启调试模式</span>
      </label>
      <label class="flex items-center gap-3 text-sm text-slate-700 cursor-pointer hover:bg-slate-100/50 rounded px-3 py-2 -my-1 transition-colors">
        <input
          v-model="options.disableSslStrict"
          type="checkbox"
          class="checkbox checkbox-sm"
        />
        <span>关闭SSL严格模式</span>
      </label>
      <div class="flex flex-wrap items-center gap-3 text-sm text-slate-700">
        <label class="flex items-center gap-3 cursor-pointer hover:bg-slate-100/50 rounded px-3 py-2 -my-1 transition-colors">
          <input
            v-model="options.forceStream"
            type="checkbox"
            class="checkbox checkbox-sm"
          />
          <span>强制流模式</span>
        </label>
        <select
          v-model="options.streamMode"
          class="select select-bordered select-sm bg-white/50"
          :disabled="!options.forceStream"
        >
          <option value="true">true</option>
          <option value="false">false</option>
        </select>
      </div>
    </div>
  </div>

  <div class="mtga-soft-panel space-y-3">
    <div>
      <div class="text-sm font-semibold text-slate-900">代理服务</div>
      <div class="text-xs text-slate-500">启动 / 停止 / 网络检查</div>
    </div>
    <div class="space-y-2">
      <button class="btn btn-primary btn-sm w-full rounded-xl shadow-sm" @click="handleStart">启动代理服务器</button>
      <button class="btn btn-outline btn-sm rounded-xl border-slate-200 text-error hover:bg-error/10 hover:border-error w-full" @click="handleStop">停止代理服务器</button>
      <button class="btn btn-outline btn-sm rounded-xl border-slate-200 hover:border-amber-500 hover:bg-amber-50/50 hover:text-amber-600 w-full" @click="handleCheck">检查网络环境</button>
    </div>
  </div>
</template>
