# 架构与依赖约束

## 分层

- UI -> actions -> services -> 领域模块（cert/hosts/network/proxy/update）-> runtime/platform
- `modules/` 根目录只保留薄 shim 或必须的 `__init__.py`。

## 依赖约束

- UI 不得直接 import 领域模块。
- actions 负责编排 services；services 定义副作用边界。
- 平台相关逻辑放在 `modules/platform`（或显式的平台子模块）。

## 重构前后对比

```mermaid
graph LR

  %% 定义样式
  classDef old fill:#f9f9f9,stroke:#333,stroke-dasharray: 5 5
  classDef ui fill:#e1f5fe,stroke:#01579b
  classDef action fill:#fff3e0,stroke:#e65100
  classDef service fill:#e8f5e9,stroke:#1b5e20
  classDef domain fill:#f3e5f5,stroke:#4a148c
  classDef infrastructure fill:#eceff1,stroke:#263238

  subgraph Before [重构前：高度耦合单体结构]
    direction TB
    GUI[mtga_gui.py]
    Modules[多个散乱的 modules]
    GUI --- Modules
    style Before fill:#fff,stroke:#999,stroke-width:2px
  end

  %% 重构演进连接
  Before == 重构为 ==> After

  subgraph After [重构后：分层领域驱动架构]
    direction TB
    
    subgraph UI_Layer [交互层]
      UI[modules/ui/*]
    end

    subgraph Logic_Layer [逻辑编排层]
      Actions[modules/actions/*]
      Services[modules/services/*]
    end

    subgraph Domain_Layer [领域逻辑层]
      DomainCert["cert/<br/>ca_store、generator"]
      DomainHosts["hosts/<br/>manager、state"]
      DomainProxy["proxy/<br/>app、runtime、transport"]
      DomainUpdate["update/<br/>checker"]
      DomainNetwork["network/<br/>environment"]
    end

    subgraph Base_Layer [基础设施与运行时]
      Runtime[modules/runtime/*]
      PlatformLayer[modules/platform/*]
    end

    %% 定义流转关系
    UI --> Actions
    Actions --> Services
    
    Services --> DomainCert
    Services --> DomainHosts
    Services --> DomainProxy
    Services --> DomainUpdate
    Services --> DomainNetwork

    DomainCert & DomainHosts & DomainProxy & DomainUpdate & DomainNetwork --> Runtime
    DomainCert & DomainProxy --> PlatformLayer

    %% 应用样式
    class UI ui
    class Actions action
    class Services service
    class DomainCert,DomainHosts,DomainProxy,DomainUpdate,DomainNetwork domain
    class Runtime,PlatformLayer infrastructure
  end
```

## 类图

```mermaid
classDiagram
  class AppBootstrapResult
  class AppContext
  class AppMetadata
  class StartupContext
  class StartupReport
  class MainWindowDepsInputs
  class MainWindowDeps
  class WindowContext
  class WindowSetupResult
  class WindowLayout
  class FontManager
  class RuntimeOptions
  class RuntimeOptionsPanelDeps
  class ConfigStore {
    +get_current_config()
    +load_global_config()
  }
  class ProxyContext
  class ProxyUiDeps
  class ProxyUiCoordinator {
    +restart_proxy()
    +stop_proxy_and_restore()
  }
  class ProxyTaskDependencies
  class ProxyTaskRunner {
    +start_proxy()
    +stop_proxy()
    +start_all()
  }
  class HostsTaskRunner {
    +modify_hosts()
    +open_hosts()
  }
  class UpdateCheckController {
    +configure()
    +trigger()
  }
  class UpdateCheckState
  class UpdateCheckDeps

  class ProxyServer {
    +start()
    +stop()
    +is_running()
  }
  class ProxyApp {
    +close()
  }
  class ProxyRuntime {
    +start()
    +stop()
    +is_running()
  }
  class RuntimeState
  class StoppableWSGIServer
  class ProxyTransport {
    +session
    +close()
  }
  class SSLContextAdapter
  class ProxyAuth {
    +verify()
    +build_forward_headers()
  }
  class ProxyConfig

  class ResourceManager
  class ThreadManager
  class OperationResult {
    +ok
    +message
    +code
  }
  class ErrorCode

  AppBootstrapResult --> AppContext
  AppBootstrapResult --> AppMetadata
  AppBootstrapResult --> StartupContext
  AppContext --> ResourceManager
  AppContext --> ThreadManager
  AppContext --> ConfigStore
  StartupContext ..> StartupReport
  MainWindowDepsInputs --> MainWindowDeps
  MainWindowDeps --> ConfigStore
  MainWindowDeps --> StartupContext
  WindowContext --> WindowLayout
  WindowSetupResult --> FontManager
  RuntimeOptionsPanelDeps --> RuntimeOptions
  ProxyContext --> RuntimeOptions
  ProxyContext --> ProxyUiCoordinator
  ProxyContext --> ProxyTaskRunner
  ProxyContext --> HostsTaskRunner
  ProxyUiCoordinator --> ProxyUiDeps
  ProxyUiCoordinator --> ConfigStore
  ProxyTaskRunner --> ProxyTaskDependencies
  ProxyTaskRunner --> ProxyUiCoordinator
  UpdateCheckController --> UpdateCheckState
  UpdateCheckController --> UpdateCheckDeps

  ProxyServer --> ProxyApp
  ProxyServer --> ProxyRuntime
  ProxyRuntime --> RuntimeState
  ProxyRuntime --> StoppableWSGIServer
  ProxyRuntime --> ResourceManager
  ProxyRuntime --> ThreadManager
  ProxyRuntime --> OperationResult
  ProxyApp --> ProxyTransport
  ProxyApp --> ProxyAuth
  ProxyApp --> ProxyConfig
  ProxyTransport --> SSLContextAdapter
  OperationResult --> ErrorCode
```

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

## 自检清单

- UI 仅通过 actions/services 访问业务能力，不直接 import 领域模块。
- 领域模块不直接操作 UI；副作用通过 services 管理。
- 平台相关实现只出现在 `modules/platform` 或显式平台子模块。
- `OperationResult` 失败时尽量填写 `ErrorCode`，避免语义漂移。
- `modules/` 根目录仅保留必要脚本与 `__init__.py`。

## 入口与依赖说明

- GUI 启动入口：`mtga_gui.py` 负责 UI 装配与流程编排。
- 配置与证书等系统资源读写通过 `services` 层触达，避免跨层访问。
