from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from modules.services import startup_checks


@dataclass(frozen=True)
class StartupContext:
    hosts_preflight_report: Any
    network_env_report: Any

    def emit_logs(
        self,
        *,
        log,
        check_environment,
        is_packaged,
    ) -> startup_checks.StartupReport:
        return startup_checks.emit_startup_logs(
            log=log,
            check_environment=check_environment,
            is_packaged=is_packaged,
            hosts_preflight_report=self.hosts_preflight_report,
            network_env_report=self.network_env_report,
        )


def build_startup_context() -> StartupContext:
    return StartupContext(
        hosts_preflight_report=startup_checks.run_hosts_preflight(),
        network_env_report=startup_checks.run_network_environment_preflight(),
    )
