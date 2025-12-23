from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass
from tkinter import messagebox, ttk
from typing import Any

from modules.proxy.proxy_config import DEFAULT_MIDDLE_ROUTE, normalize_middle_route
from modules.services.config_service import ConfigStore


@dataclass(frozen=True)
class ConfigGroupPanelDeps:
    parent: ttk.Frame
    window: tk.Tk
    log: Callable[[str], None]
    tooltip: Callable[..., None]
    center_window: Callable[[tk.Toplevel | tk.Tk], None]
    get_preferred_font: Callable[..., Any]
    config_store: ConfigStore
    thread_manager: Any
    api_key_visible_chars: int
    test_chat_completion: Callable[..., None]
    test_model_in_list: Callable[..., None]


class ConfigGroupPanel:
    def __init__(self, deps: ConfigGroupPanelDeps) -> None:
        self._deps = deps
        self._config_groups: list[dict[str, Any]] = []
        self._current_config_index = 0
        self._build()
        self.refresh_config_list()

    def refresh_config_list(self) -> None:
        self._refresh_config_tree()
        self._deps.log("已刷新配置组列表")

    def _build(self) -> None:
        config_frame = ttk.LabelFrame(self._deps.parent, text="代理服务器配置组")
        config_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        config_paned = ttk.PanedWindow(config_frame, orient=tk.HORIZONTAL)
        config_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        config_list_frame = ttk.Frame(config_paned)
        config_paned.add(config_list_frame, weight=3)

        list_header_frame = ttk.Frame(config_list_frame)
        list_header_frame.pack(fill=tk.X, padx=5, pady=(5, 0))

        ttk.Label(list_header_frame, text="配置组列表:").pack(side=tk.LEFT)

        test_btn = ttk.Button(
            list_header_frame,
            text="测活",
            command=self._test_selected_config,
            width=6,
        )
        test_btn.pack(side=tk.RIGHT, padx=5)
        self._deps.tooltip(
            test_btn,
            "测试选中配置组的实际对话功能\n会发送最小请求并消耗少量tokens\n请确保配置正确后使用",
            wraplength=250,
        )

        refresh_btn = ttk.Button(
            list_header_frame,
            text="刷新",
            command=self.refresh_config_list,
            width=6,
        )
        refresh_btn.pack(side=tk.RIGHT, padx=16)
        self._deps.tooltip(
            refresh_btn,
            "重新加载配置文件中的配置组\n用于同步外部修改或恢复意外更改",
            wraplength=250,
        )

        tree_frame = ttk.Frame(config_list_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ("序号", "API URL", "实际模型ID", "API Key")
        self._config_tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings", height=6
        )

        v_scrollbar = ttk.Scrollbar(
            tree_frame,
            orient=tk.VERTICAL,
            command=self._config_tree.yview,
        )
        self._config_tree.configure(yscrollcommand=v_scrollbar.set)
        h_scrollbar = ttk.Scrollbar(
            tree_frame,
            orient=tk.HORIZONTAL,
            command=self._config_tree.xview,
        )
        self._config_tree.configure(xscrollcommand=h_scrollbar.set)

        self._config_tree.heading("序号", text="序号")
        self._config_tree.heading("API URL", text="API URL")
        self._config_tree.heading("实际模型ID", text="实际模型ID")
        self._config_tree.heading("API Key", text="API Key")

        self._config_tree.column("序号", width=30, anchor=tk.CENTER)
        self._config_tree.column("API URL", width=200)
        self._config_tree.column("实际模型ID", width=120)
        self._config_tree.column("API Key", width=120)

        self._config_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        config_buttons_frame = ttk.Frame(config_paned)
        config_paned.add(config_buttons_frame, weight=1)

        ttk.Label(config_buttons_frame, text="操作:").pack(anchor=tk.W, padx=5, pady=(5, 0))

        ttk.Button(config_buttons_frame, text="新增", command=self._add_config_group).pack(
            fill=tk.X, padx=5, pady=2
        )
        ttk.Button(config_buttons_frame, text="修改", command=self._edit_config_group).pack(
            fill=tk.X, padx=5, pady=2
        )
        ttk.Button(config_buttons_frame, text="删除", command=self._delete_config_group).pack(
            fill=tk.X, padx=5, pady=2
        )
        ttk.Button(config_buttons_frame, text="上移", command=self._move_config_up).pack(
            fill=tk.X, padx=5, pady=2
        )
        ttk.Button(config_buttons_frame, text="下移", command=self._move_config_down).pack(
            fill=tk.X, padx=5, pady=2
        )

        self._config_tree.bind("<<TreeviewSelect>>", self._on_config_select)

    def _test_selected_config(self) -> None:
        selected_index = self._get_selected_index()
        if selected_index < 0:
            self._deps.log("请先选择要测活的配置组")
            return

        config_group = self._config_groups[selected_index]
        self._deps.test_chat_completion(
            config_group,
            log_func=self._deps.log,
            thread_manager=self._deps.thread_manager,
        )

    def _refresh_config_tree(self) -> None:
        (
            self._config_groups,
            self._current_config_index,
        ) = self._deps.config_store.load_config_groups()

        for item in self._config_tree.get_children():
            self._config_tree.delete(item)

        for i, group in enumerate(self._config_groups):
            if "target_model_id" in group:
                fourth_col = group.get("target_model_id", "") or "(无)"
            else:
                api_key = group.get("api_key", "")
                if api_key:
                    if len(api_key) > self._deps.api_key_visible_chars:
                        mask = "*" * (len(api_key) - self._deps.api_key_visible_chars)
                        suffix = api_key[-self._deps.api_key_visible_chars :]
                        fourth_col = f"{mask}{suffix}"
                    else:
                        fourth_col = "***"
                else:
                    fourth_col = "(无)"

            self._config_tree.insert(
                "",
                "end",
                values=(i + 1, group.get("api_url", ""), group.get("model_id", ""), fourth_col),
            )

        if self._config_groups and 0 <= self._current_config_index < len(self._config_groups):
            children = self._config_tree.get_children()
            if self._current_config_index < len(children):
                self._config_tree.selection_set(children[self._current_config_index])
                self._config_tree.focus(children[self._current_config_index])

    def _get_selected_index(self) -> int:
        selection = self._config_tree.selection()
        if selection:
            item = selection[0]
            return self._config_tree.index(item)
        return -1

    def _on_config_select(self, _event) -> None:
        selected_index = self._get_selected_index()
        if selected_index >= 0:
            self._current_config_index = selected_index
            self._deps.config_store.save_config_groups(
                self._config_groups,
                self._current_config_index,
            )

    def _open_config_group_window(  # noqa: PLR0915
        self,
        title: str,
        initial_group: dict[str, Any] | None,
        on_save: Callable[[dict[str, str]], bool],
        on_saved: Callable[[dict[str, str]], None] | None = None,
    ) -> None:
        def handle_save() -> None:
            name = name_var.get().strip()
            api_url = api_url_var.get().strip()
            model_id = model_id_var.get().strip()
            api_key = api_key_var.get().strip()
            middle_route_value = ""
            if middle_route_enabled_var.get() and not placeholder_active:
                middle_route_value = middle_route_var.get().strip()

            if not api_url or not model_id or not api_key:
                self._deps.log("错误: API URL、实际模型ID和API Key都是必填项")
                return

            payload = {
                "name": name,
                "api_url": api_url,
                "model_id": model_id,
                "api_key": api_key,
            }
            if middle_route_value:
                payload["middle_route"] = normalize_middle_route(middle_route_value)

            if on_save(payload):
                window.destroy()
                if on_saved:
                    on_saved(payload)

        window = tk.Toplevel(self._deps.window)
        window.title(title)
        window.geometry("450x330")
        window.resizable(False, False)
        window.transient(self._deps.window)

        main_frame = ttk.Frame(window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        name_value = initial_group.get("name", "") if initial_group else ""
        api_url_value = initial_group.get("api_url", "") if initial_group else ""
        model_id_value = initial_group.get("model_id", "") if initial_group else ""
        api_key_value = initial_group.get("api_key", "") if initial_group else ""

        ttk.Label(main_frame, text="配置组名称 (可选):").grid(row=0, column=0, sticky=tk.W, pady=5)
        name_var = tk.StringVar(value=name_value)
        name_entry = ttk.Entry(main_frame, textvariable=name_var, width=35)
        name_entry.grid(row=0, column=1, sticky=tk.EW, padx=(10, 0), pady=5)

        ttk.Label(main_frame, text="* API URL:").grid(row=1, column=0, sticky=tk.W, pady=5)
        api_url_var = tk.StringVar(value=api_url_value)
        api_url_entry = ttk.Entry(main_frame, textvariable=api_url_var, width=35)
        api_url_entry.grid(row=1, column=1, sticky=tk.EW, padx=(10, 0), pady=5)

        middle_route_value = initial_group.get("middle_route", "").strip() if initial_group else ""
        middle_route_enabled_var = tk.BooleanVar(value=bool(middle_route_value))
        middle_route_var = tk.StringVar(value=middle_route_value)
        middle_route_custom_value = middle_route_value
        placeholder_active = False

        placeholder_style = "ConfigGroupPlaceholder.TEntry"
        ttk.Style().configure(placeholder_style, foreground="gray")

        middle_route_toggle = ttk.Checkbutton(
            main_frame,
            text="修改中间路由",
            variable=middle_route_enabled_var,
        )
        middle_route_toggle.grid(row=2, column=0, sticky=tk.W, pady=5)

        middle_route_entry = ttk.Entry(main_frame, textvariable=middle_route_var, width=35)
        middle_route_entry.grid(row=2, column=1, sticky=tk.EW, padx=(10, 0), pady=5)

        ttk.Label(main_frame, text="* 实际模型ID:").grid(row=3, column=0, sticky=tk.W, pady=5)
        model_id_var = tk.StringVar(value=model_id_value)
        model_id_entry = ttk.Entry(main_frame, textvariable=model_id_var, width=35)
        model_id_entry.grid(row=3, column=1, sticky=tk.EW, padx=(10, 0), pady=5)

        ttk.Label(main_frame, text="* API Key:").grid(row=4, column=0, sticky=tk.W, pady=5)
        api_key_var = tk.StringVar(value=api_key_value)
        api_key_entry = ttk.Entry(main_frame, textvariable=api_key_var, width=35, show="*")
        api_key_entry.grid(row=4, column=1, sticky=tk.EW, padx=(10, 0), pady=5)

        def set_middle_route_placeholder() -> None:
            nonlocal placeholder_active
            middle_route_var.set(DEFAULT_MIDDLE_ROUTE)
            middle_route_entry.configure(style=placeholder_style)
            placeholder_active = True

        def clear_middle_route_placeholder() -> None:
            nonlocal placeholder_active
            if placeholder_active:
                middle_route_var.set("")
                middle_route_entry.configure(style="TEntry")
                placeholder_active = False

        def apply_middle_route_state() -> None:
            nonlocal middle_route_custom_value, placeholder_active
            if middle_route_enabled_var.get():
                middle_route_entry.configure(state="normal")
                if middle_route_custom_value:
                    middle_route_var.set(middle_route_custom_value)
                    middle_route_entry.configure(style="TEntry")
                    placeholder_active = False
                else:
                    set_middle_route_placeholder()
            else:
                if not placeholder_active:
                    middle_route_custom_value = middle_route_var.get().strip()
                middle_route_entry.configure(state="disabled")
                set_middle_route_placeholder()

        def on_middle_route_focus_in(_event: tk.Event) -> None:
            if middle_route_enabled_var.get() and placeholder_active:
                clear_middle_route_placeholder()

        def on_middle_route_focus_out(_event: tk.Event) -> None:
            if not middle_route_enabled_var.get():
                return
            if not middle_route_var.get().strip():
                set_middle_route_placeholder()

        def on_middle_route_key_release(_event: tk.Event) -> None:
            nonlocal middle_route_custom_value
            if not middle_route_enabled_var.get() or placeholder_active:
                return
            middle_route_custom_value = middle_route_var.get().strip()

        middle_route_toggle.configure(command=apply_middle_route_state)
        middle_route_entry.bind("<FocusIn>", on_middle_route_focus_in)
        middle_route_entry.bind("<FocusOut>", on_middle_route_focus_out)
        middle_route_entry.bind("<KeyRelease>", on_middle_route_key_release)
        apply_middle_route_state()

        info_label = ttk.Label(
            main_frame,
            text="* 为必填项",
            font=self._deps.get_preferred_font(size=8),
            foreground="gray",
        )
        info_label.grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=5)

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="保存", command=handle_save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=window.destroy).pack(
            side=tk.LEFT, padx=5
        )

        main_frame.columnconfigure(1, weight=1)
        self._deps.center_window(window)
        window.grab_set()
        name_entry.focus()

    def _add_config_group(self) -> None:
        def save_new_config(payload: dict[str, str]) -> bool:
            self._config_groups.append(payload)
            if self._deps.config_store.save_config_groups(
                self._config_groups, self._current_config_index
            ):
                display_name = payload["name"] or f"配置组 {len(self._config_groups)}"
                self._deps.log(f"已添加配置组: {display_name}")
                self.refresh_config_list()
                return True

            self._deps.log("保存配置组失败")
            return False

        def after_save(payload: dict[str, str]) -> None:
            self._deps.test_model_in_list(
                payload,
                log_func=self._deps.log,
                thread_manager=self._deps.thread_manager,
            )

        self._open_config_group_window(
            title="新增配置组",
            initial_group=None,
            on_save=save_new_config,
            on_saved=after_save,
        )

    def _edit_config_group(self) -> None:
        selected_index = self._get_selected_index()
        if selected_index < 0:
            self._deps.log("请先选择要修改的配置组")
            return

        current_group = self._config_groups[selected_index]

        def save_edited_config(payload: dict[str, str]) -> bool:
            self._config_groups[selected_index] = payload
            if self._deps.config_store.save_config_groups(
                self._config_groups, self._current_config_index
            ):
                display_name = payload["name"] or f"配置组 {selected_index + 1}"
                self._deps.log(f"已修改配置组: {display_name}")
                self.refresh_config_list()
                return True

            self._deps.log("保存配置组失败")
            return False

        def after_save(payload: dict[str, str]) -> None:
            self._deps.test_model_in_list(
                payload,
                log_func=self._deps.log,
                thread_manager=self._deps.thread_manager,
            )

        self._open_config_group_window(
            title="修改配置组",
            initial_group=current_group,
            on_save=save_edited_config,
            on_saved=after_save,
        )

    def _delete_config_group(self) -> None:
        selected_index = self._get_selected_index()
        if selected_index < 0:
            self._deps.log("请先选择要删除的配置组")
            return

        if len(self._config_groups) <= 1:
            self._deps.log("至少需要保留一个配置组")
            return

        group_name = self._config_groups[selected_index].get(
            "name", f"配置组{selected_index + 1}"
        )

        if messagebox.askyesno("确认删除", f"确定要删除配置组 '{group_name}' 吗？"):
            del self._config_groups[selected_index]

            if self._current_config_index >= len(self._config_groups):
                self._current_config_index = len(self._config_groups) - 1
            elif self._current_config_index > selected_index:
                self._current_config_index -= 1

            if self._deps.config_store.save_config_groups(
                self._config_groups, self._current_config_index
            ):
                self._deps.log(f"已删除配置组: {group_name}")
                self.refresh_config_list()
            else:
                self._deps.log("保存配置组失败")

    def _move_config_up(self) -> None:
        selected_index = self._get_selected_index()
        if selected_index <= 0:
            return

        self._config_groups[selected_index], self._config_groups[selected_index - 1] = (
            self._config_groups[selected_index - 1],
            self._config_groups[selected_index],
        )

        if self._current_config_index == selected_index:
            self._current_config_index = selected_index - 1
        elif self._current_config_index == selected_index - 1:
            self._current_config_index = selected_index

        if self._deps.config_store.save_config_groups(
            self._config_groups, self._current_config_index
        ):
            self.refresh_config_list()
            children = self._config_tree.get_children()
            if selected_index - 1 < len(children):
                self._config_tree.selection_set(children[selected_index - 1])
                self._config_tree.focus(children[selected_index - 1])
        else:
            self._deps.log("保存配置组失败")

    def _move_config_down(self) -> None:
        selected_index = self._get_selected_index()
        if selected_index < 0 or selected_index >= len(self._config_groups) - 1:
            return

        self._config_groups[selected_index], self._config_groups[selected_index + 1] = (
            self._config_groups[selected_index + 1],
            self._config_groups[selected_index],
        )

        if self._current_config_index == selected_index:
            self._current_config_index = selected_index + 1
        elif self._current_config_index == selected_index + 1:
            self._current_config_index = selected_index

        if self._deps.config_store.save_config_groups(
            self._config_groups, self._current_config_index
        ):
            self.refresh_config_list()
            children = self._config_tree.get_children()
            if selected_index + 1 < len(children):
                self._config_tree.selection_set(children[selected_index + 1])
                self._config_tree.focus(children[selected_index + 1])
        else:
            self._deps.log("保存配置组失败")


def build_config_group_panel(deps: ConfigGroupPanelDeps) -> ConfigGroupPanel:
    return ConfigGroupPanel(deps)
