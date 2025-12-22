# 架构与依赖约束

## 分层

- UI -> actions -> services -> 领域模块（cert/hosts/network/proxy/update）-> runtime/platform
- `modules/` 根目录只保留薄 shim 或必须的 `__init__.py`。

## 依赖约束

- UI 不得直接 import 领域模块。
- actions 负责编排 services；services 定义副作用边界。
- 平台相关逻辑放在 `modules/platform`（或显式的平台子模块）。

## 错误处理

- 在 service/action 边界使用 `OperationResult`。
- 字段：
  - `ok`：成功标记
  - `message`：人类可读摘要
  - `code`：`ErrorCode` 枚举值（可选）
  - `details`：结构化上下文载荷

### 错误码（核心）

- `NETWORK_ERROR`
- `REMOTE_ERROR`
- `NO_VERSION`
- `BACKUP_DIR_MISSING`
- `NO_BACKUPS`
- `CONFIG_INVALID`
- `FILE_NOT_FOUND`
- `PERMISSION_DENIED`
- `PORT_IN_USE`
- `UNKNOWN`

### 示例

```python
from modules.runtime.error_codes import ErrorCode
from modules.runtime.operation_result import OperationResult

def example_call() -> OperationResult:
    return OperationResult.failure(
        "Request failed",
        code=ErrorCode.NETWORK_ERROR,
        retry_after=30,
    )
```
