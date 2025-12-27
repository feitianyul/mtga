<template>
  <div class="card bg-base-200 shadow-sm">
    <div class="card-body p-4">
      <div class="flex items-center justify-between">
        <h2 class="card-title text-base">代理服务器配置组</h2>
        <div class="flex gap-2">
          <button class="btn btn-sm">测活</button>
          <button class="btn btn-sm">刷新</button>
        </div>
      </div>

      <div class="mt-3 grid gap-4 lg:grid-cols-[1fr,160px]">
        <div class="overflow-auto rounded bg-base-100">
          <table class="table table-sm">
            <thead>
              <tr>
                <th>序号</th>
                <th>API URL</th>
                <th>实际模型ID</th>
                <th>API Key</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>1</td>
                <td>https://api.example.com</td>
                <td>gpt-5</td>
                <td>********</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="space-y-2">
          <button class="btn btn-sm w-full">新增</button>
          <button class="btn btn-sm w-full">修改</button>
          <button class="btn btn-sm w-full">删除</button>
          <button class="btn btn-sm w-full">上移</button>
          <button class="btn btn-sm w-full">下移</button>
        </div>
      </div>
    </div>
  </div>
</template>
