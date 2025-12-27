<template>
  <div class="card bg-base-200 shadow-sm">
    <div class="card-body p-4">
      <h2 class="card-title text-base">全局配置</h2>
      <div class="mt-3 space-y-3">
        <label class="form-control">
          <div class="label">
            <span class="label-text">映射模型ID</span>
          </div>
          <input class="input input-bordered w-full" placeholder="例如：gpt-5" />
        </label>

        <label class="form-control">
          <div class="label">
            <span class="label-text">MTGA鉴权Key</span>
          </div>
          <input class="input input-bordered w-full" placeholder="例如：111" />
        </label>

        <div>
          <button class="btn btn-primary btn-sm">保存全局配置</button>
        </div>
      </div>
    </div>
  </div>
</template>
