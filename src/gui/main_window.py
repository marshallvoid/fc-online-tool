import asyncio
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING, Any, Optional

import darkdetect
import sv_ttk

from src.core.main_tool import MainTool
from src.gui.components import ActivityLogTab, EventTab
from src.utils.contants import EVENT_CONFIGS_MAP

if TYPE_CHECKING:
    from src.schemas import UserInfo


class MainWindow:
    def __init__(self) -> None:
        self._root = tk.Tk()
        self._root.title("FC Online Automation Tool")
        self._root.geometry("700x700")
        self._root.resizable(False, False)
        self._root.minsize(700, 650)

        self._username_var = tk.StringVar(value="")
        self._password_var = tk.StringVar(value="")
        self._spin_action_var = tk.IntVar(value=1)
        self._target_special_jackpot_var = tk.IntVar(value=10000)

        self._username_var.trace_add(
            "write",
            lambda *_: (
                self._tool_instance.update_credentials(self._username_var.get(), self._password_var.get())
                if not self._is_running
                else None
            ),
        )
        self._password_var.trace_add(
            "write",
            lambda *_: (
                self._tool_instance.update_credentials(self._username_var.get(), self._password_var.get())
                if not self._is_running
                else None
            ),
        )

        self._is_running = False
        self._selected_event = "Bi Lắc"
        self._tool_instance = MainTool(
            event_config=EVENT_CONFIGS_MAP[self._selected_event],
            username=self._username_var.get(),
            password=self._password_var.get(),
            spin_action=self._spin_action_var.get(),
            target_special_jackpot=self._target_special_jackpot_var.get(),
        )

        self._setup_ui()

    def _setup_ui(self) -> None:
        control_frame = ttk.Frame(self._root)
        control_frame.pack(side="bottom", fill="x", padx=10, pady=(5, 10))

        self._start_btn = ttk.Button(
            control_frame,
            text="Start",
            command=self._handle_start_button,
            style="Accent.TButton",
        )
        self._start_btn.pack(side="left", padx=(0, 5))

        self._stop_btn = ttk.Button(
            control_frame,
            text="Stop",
            command=self._handle_stop_button,
            state="disabled",
        )
        self._stop_btn.pack(side="left", padx=5)

        self._status_label = ttk.Label(control_frame, text="✅ Status: Ready")
        self._status_label.pack(side="right")

        main_container = ttk.Frame(self._root)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)

        self._notebook = ttk.Notebook(main_container, takefocus=False)
        self._notebook.pack(fill="both", expand=True)

        self._bilac_tab = EventTab(
            parent=self._notebook,
            title="Bi Lắc",
            username_var=self._username_var,
            password_var=self._password_var,
            target_special_jackpot_var=self._target_special_jackpot_var,
            spin_action_var=self._spin_action_var,
            on_spin_action_changed=lambda: setattr(self._tool_instance, "spin_action", self._spin_action_var.get()),
        )
        self._notebook.add(self._bilac_tab.frame, text="Bi Lắc")

        self._typhu_tab = EventTab(
            parent=self._notebook,
            title="Tỷ Phú",
            username_var=self._username_var,
            password_var=self._password_var,
            target_special_jackpot_var=self._target_special_jackpot_var,
            spin_action_var=self._spin_action_var,
            on_spin_action_changed=lambda: setattr(self._tool_instance, "spin_action", self._spin_action_var.get()),
        )
        self._notebook.add(self._typhu_tab.frame, text="Tỷ Phú")

        self._activity_log_tab = ActivityLogTab(parent=self._notebook)
        self._notebook.add(self._activity_log_tab.frame, text="Activity Log")

        self._update_spin_labels_for_tab(self._selected_event)

        self._focus_after_id: Optional[str] = None

        def _schedule_focus_current_tab() -> None:
            def _focus_current_tab() -> None:
                try:
                    current = self._notebook.nametowidget(self._notebook.select())
                    if current and isinstance(current, (tk.Frame, ttk.Frame)):
                        current.focus_set()

                except Exception:
                    pass

            if self._focus_after_id:
                try:
                    self._root.after_cancel(self._focus_after_id)
                except Exception:
                    pass
                finally:
                    self._focus_after_id = None

            self._focus_after_id = self._root.after(10, _focus_current_tab)

        def _on_tab_changed(_: object) -> None:
            try:
                current_index = self._notebook.index(self._notebook.select())
                tab_text = self._notebook.tab(current_index, "text")
                if not self._is_running:
                    self._selected_event = tab_text
                    # Update spin labels when tab changes
                    self._update_spin_labels_for_tab(tab_text)

            except Exception:
                pass

            _schedule_focus_current_tab()

        self._notebook.bind("<<NotebookTabChanged>>", _on_tab_changed)
        self._notebook.bind("<ButtonRelease-1>", lambda e: _schedule_focus_current_tab())
        self._root.after_idle(_schedule_focus_current_tab)

    def _update_spin_labels_for_tab(self, tab_name: str) -> None:
        if tab_name not in EVENT_CONFIGS_MAP:
            return

        target_tab = None
        match tab_name:
            case "Bi Lắc":
                target_tab = self._bilac_tab
            case "Tỷ Phú":
                target_tab = self._typhu_tab
            case _:
                pass

        if target_tab is None:
            return

        target_tab.update_spin_labels(spin_action_selectors=EVENT_CONFIGS_MAP[tab_name].spin_action_selectors)

    def _update_user_panel(self, user_info: Optional["UserInfo"]) -> None:
        info_text = (
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔒 NOT LOGGED IN\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "   Please enter your credentials and start the tool"
        )

        if user_info and user_info.payload.user:
            info_text = (
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 ACCOUNT INFORMATION\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"User ID    : {user_info.payload.user.uid}\n"
                f"Username   : {user_info.payload.user.nickname}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💰 CURRENCY & RESOURCES\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Free Spins : {user_info.payload.user.free_spin:,}\n"
                f"FC Points  : {user_info.payload.user.fc:,}\n"
                f"MC Points  : {user_info.payload.user.mc:,}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🎰 SPECIAL JACKPOT: {self._tool_instance.special_jackpot:,} 💰\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            )

        current_index = self._notebook.index(self._notebook.select())
        tab_text = self._notebook.tab(current_index, "text")

        match tab_text:
            case "Bi Lắc":
                self._bilac_tab.update_user_info_text(info_text, foreground="#4caf50")
            case "Tỷ Phú":
                self._typhu_tab.update_user_info_text(info_text, foreground="#4caf50")
            case _:
                pass

    def _handle_stop_task(self) -> None:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            loop.run_until_complete(self._tool_instance.close())
            loop.close()

            self._status_label.config(text="✅ Status: Ready")

        except Exception as error:
            error_msg = f"❌ Error: {str(error)}"
            self._root.after(0, lambda: messagebox.showerror("❌ Error", error_msg))

    def _handle_stop_button(self) -> None:
        if not self._is_running:
            return

        self._is_running = False
        self._start_btn.config(state="normal")
        self._stop_btn.config(state="disabled")
        self._status_label.config(text="⏹️ Status: Stopping...")
        self._bilac_tab.set_enabled(True)
        self._typhu_tab.set_enabled(True)

        self._tool_instance.stop_flag = True

        threading.Thread(target=self._handle_stop_task, daemon=True).start()

    def _handle_launch_task(self) -> None:
        try:
            self._root.after(0, lambda: self._status_label.config(text="🚀 Status: Starting..."))

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            loop.run_until_complete(self._tool_instance.run())

        except Exception as error:
            error_msg = f"❌ Error: {str(error)}"
            self._root.after(0, lambda: messagebox.showerror("❌ Error", error_msg))
            self._is_running = False
            self._start_btn.config(state="normal")
            self._stop_btn.config(state="disabled")
            self._status_label.config(text="✅ Status: Ready")
            self._bilac_tab.set_enabled(True)
            self._typhu_tab.set_enabled(True)

    def _handle_start_button(self) -> None:
        if self._is_running:
            return

        if not self._username_var.get().strip():
            messagebox.showerror("❌ Error", "Username cannot be empty!")
            return

        if not self._password_var.get().strip():
            messagebox.showerror("❌ Error", "Password cannot be empty!")
            return

        try:
            target_value = self._target_special_jackpot_var.get()
            if target_value <= 0:
                msg = "Target Jackpot must be a positive number!"
                raise ValueError(msg)

        except ValueError as error:
            messagebox.showerror("❌ Error", str(error))
            return

        self._is_running = True
        self._start_btn.config(state="disabled")
        self._stop_btn.config(state="normal")
        self._status_label.config(text="🚀 Status: Starting...")
        self._bilac_tab.set_enabled(enabled=False)
        self._typhu_tab.set_enabled(enabled=False)

        widget = self._activity_log_tab.messages_text_widget
        widget.config(state="normal")
        widget.delete("1.0", tk.END)
        widget.config(state="disabled")

        self._tool_instance.event_config = EVENT_CONFIGS_MAP[self._selected_event]
        self._tool_instance.spin_action = self._spin_action_var.get()
        self._tool_instance.target_special_jackpot = self._target_special_jackpot_var.get()

        self._tool_instance.stop_flag = False
        self._tool_instance.special_jackpot = 0
        self._tool_instance.mini_jackpot = 0

        def message_callback(tag: str, message: str) -> None:
            self._root.after(0, lambda: self._activity_log_tab.add_message(tag=tag, message=message))

        def user_panel_callback(user_info: Optional["UserInfo"]) -> None:
            self._root.after(0, lambda: self._update_user_panel(user_info=user_info))

        self._tool_instance.message_callback = message_callback
        self._tool_instance.user_panel_callback = user_panel_callback

        threading.Thread(target=self._handle_launch_task, daemon=True).start()

    def run(self) -> None:
        def on_close() -> None:
            if self._is_running:
                self._tool_instance.stop_flag = True

            self._root.destroy()

        self._root.protocol("WM_DELETE_WINDOW", on_close)

        sv_ttk.set_theme(darkdetect.theme() or "dark")

        try:
            style = ttk.Style(self._root)
            layout = style.layout("TNotebook.Tab")

            def _strip_focus(elements: Any) -> Any:
                if not isinstance(elements, (list, tuple)):
                    return elements

                cleaned = []
                for elem in elements:
                    if isinstance(elem, tuple) and elem:
                        name = elem[0]
                        opts = elem[1] if len(elem) > 1 else {}

                        if isinstance(name, str) and name.endswith(".focus"):
                            continue

                        if isinstance(opts, dict) and "children" in opts:
                            opts = dict(opts)
                            opts["children"] = _strip_focus(opts.get("children", []))
                            cleaned.append((name, opts))
                            continue

                        cleaned.append(elem)
                        continue

                    cleaned.append(elem)

                return cleaned

            cleaned_layout = _strip_focus(layout)
            style.layout("TNotebook.Tab", cleaned_layout)

        except Exception:
            pass

        self._root.mainloop()
