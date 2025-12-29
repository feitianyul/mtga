from __future__ import annotations

from functools import lru_cache
from typing import Any, Literal

from modules.actions import model_tests
from modules.runtime.operation_result import OperationResult
from modules.runtime.resource_manager import ResourceManager
from modules.services.config_service import ConfigStore
from pydantic import BaseModel
from pytauri import Commands

from .common import build_result_payload, collect_logs


class InlineThreadManager:
    def run(self, name: str, target, *args, **kwargs) -> str:
        target(*args, **kwargs)
        return f"{name}-inline"

    def wait(self, _task_id: str | None, _timeout: float | None = None) -> bool:
        return True


class ConfigGroupTestPayload(BaseModel):
    index: int
    mode: Literal["chat", "models"] = "chat"


@lru_cache(maxsize=1)
def _get_resource_manager() -> ResourceManager:
    return ResourceManager()


@lru_cache(maxsize=1)
def _get_config_store() -> ConfigStore:
    resource_manager = _get_resource_manager()
    return ConfigStore(resource_manager.get_user_config_file())


def register_model_test_commands(commands: Commands) -> None:
    @commands.command()
    async def config_group_test(body: ConfigGroupTestPayload) -> dict[str, Any]:
        logs, log_func = collect_logs()
        config_store = _get_config_store()
        config_groups, _ = config_store.load_config_groups()
        if not config_groups:
            result = OperationResult.failure("没有可用的配置组")
            return build_result_payload(result, logs, "配置组测活失败")
        if body.index < 0 or body.index >= len(config_groups):
            result = OperationResult.failure("配置组索引无效")
            return build_result_payload(result, logs, "配置组测活失败")
        group = config_groups[body.index]
        if not isinstance(group, dict):
            result = OperationResult.failure("配置组数据不正确")
            return build_result_payload(result, logs, "配置组测活失败")

        thread_manager = InlineThreadManager()
        if body.mode == "models":
            model_tests.test_model_in_list(
                group,
                log_func=log_func,
                thread_manager=thread_manager,
            )
        else:
            model_tests.test_chat_completion(
                group,
                log_func=log_func,
                thread_manager=thread_manager,
            )
        result = OperationResult.success()
        return build_result_payload(result, logs, "配置组测活完成")
