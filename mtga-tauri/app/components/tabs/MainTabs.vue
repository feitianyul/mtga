<template>
  <div class="card bg-base-200 shadow-sm">
    <div class="card-body p-4">
      <div role="tablist" class="tabs tabs-bordered">
        <a role="tab" class="tab tab-active">证书管理</a>
        <a role="tab" class="tab">hosts文件管理</a>
        <a role="tab" class="tab">代理服务器操作</a>
        <a role="tab" class="tab">用户数据管理</a>
        <a role="tab" class="tab">关于</a>
      </div>

      <div class="mt-4">
        <slot />
      </div>
    </div>
  </div>
</template>
