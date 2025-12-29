<script setup lang="ts">
const store = useMtgaStore()
const options = store.runtimeOptions
</script>

<template>
  <div class="card bg-base-200 shadow-sm">
    <div class="card-body p-4">
      <h2 class="card-title text-base">运行时选项</h2>
      <div class="mt-3 space-y-3">
        <label class="flex items-center gap-2">
          <input v-model="options.debugMode" type="checkbox" class="checkbox checkbox-sm" />
          <span>开启调试模式</span>
        </label>
        <label class="flex items-center gap-2">
          <input
            v-model="options.disableSslStrict"
            type="checkbox"
            class="checkbox checkbox-sm"
          />
          <span>关闭SSL严格模式</span>
        </label>
        <div class="flex items-center gap-3">
          <label class="flex items-center gap-2">
            <input
              v-model="options.forceStream"
              type="checkbox"
              class="checkbox checkbox-sm"
            />
            <span>强制流模式</span>
          </label>
          <select
            v-model="options.streamMode"
            class="select select-bordered select-sm"
            :disabled="!options.forceStream"
          >
            <option value="true">true</option>
            <option value="false">false</option>
          </select>
        </div>
      </div>
    </div>
  </div>
</template>
