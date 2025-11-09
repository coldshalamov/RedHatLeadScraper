"""Tkinter based desktop application for the lead verifier."""
from __future__ import annotations

import itertools
import queue
import tkinter as tk
from dataclasses import dataclass
from tkinter import filedialog, messagebox, ttk
from typing import Dict, Iterable, List, Optional

from ..ingestion import export_to_csv, export_to_excel
from ..models import LeadVerificationResult
from ..orchestrator import LeadVerifierOrchestrator, LeadVerificationTask


@dataclass
class SourceStyle:
    """Simple structure describing row styling for a source."""

    background: str
    foreground: str = "#000000"


class MappingFrame(ttk.LabelFrame):
    """Widget that lets the user match spreadsheet columns to known fields."""

    FIELD_LABELS = {
        "name": "Full name *",
        "phone": "Phone",
        "email": "Email",
        "company": "Company",
        "city": "City",
    }

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, text="2. Column mapping")
        self.variables: Dict[str, tk.StringVar] = {}
        self.comboboxes: Dict[str, ttk.Combobox] = {}
        self._build()

    # ------------------------------------------------------------------
    def _build(self) -> None:
        for row_index, (field_key, label) in enumerate(self.FIELD_LABELS.items()):
            ttk.Label(self, text=label).grid(row=row_index, column=0, sticky="w", padx=4, pady=4)
            variable = tk.StringVar()
            combobox = ttk.Combobox(self, textvariable=variable, state="readonly")
            combobox.grid(row=row_index, column=1, sticky="ew", padx=4, pady=4)
            combobox["values"] = ("",)
            self.variables[field_key] = variable
            self.comboboxes[field_key] = combobox
        self.columnconfigure(1, weight=1)

    # ------------------------------------------------------------------
    def update_options(self, columns: Iterable[str]) -> None:
        values = [""] + list(columns)
        for field, combobox in self.comboboxes.items():
            combobox["values"] = values
            current = combobox.get()
            if current not in values:
                combobox.set("")
        # Auto-select exact matches for convenience
        for column in columns:
            lowered = column.lower()
            for field in self.FIELD_LABELS:
                if field in {"company", "city"}:
                    if lowered == field:
                        self.comboboxes[field].set(column)
                elif lowered == field or lowered.replace(" ", "") == field:
                    self.comboboxes[field].set(column)

    # ------------------------------------------------------------------
    def get_mapping(self) -> Dict[str, str]:
        return {field: variable.get() for field, variable in self.variables.items() if variable.get()}


class LeadVerifierApp:
    """Main application window."""

    SOURCE_COLORS = [
        SourceStyle("#E3F2FD"),
        SourceStyle("#FCE4EC"),
        SourceStyle("#E8F5E9"),
        SourceStyle("#FFF3E0"),
        SourceStyle("#EDE7F6"),
    ]

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Lead Verifier")
        self.root.geometry("1024x720")
        self.root.minsize(900, 640)

        self.orchestrator = LeadVerifierOrchestrator()
        self.event_queue: "queue.Queue[tuple]" = queue.Queue()
        self.current_task: Optional[LeadVerificationTask] = None
        self.loaded_rows: List[Dict[str, str]] = []
        self.result_rows: List[LeadVerificationResult] = []
        self.source_styles: Dict[str, SourceStyle] = {}
        self._color_cycle = itertools.cycle(self.SOURCE_COLORS)

        self.file_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Idle")
        self.progress_var = tk.DoubleVar(value=0.0)
        self.filter_var = tk.StringVar()
        self.filter_var.trace_add("write", lambda *_: self.refresh_result_table())

        self._build_layout()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.after(100, self._poll_queue)

    # ------------------------------------------------------------------
    def _build_layout(self) -> None:
        container = ttk.Frame(self.root, padding=12)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)

        self._build_import_section(container)
        self.mapping_frame = MappingFrame(container)
        self.mapping_frame.grid(row=1, column=0, sticky="nsew", pady=(12, 0))

        self._build_progress_section(container)
        self._build_results_section(container)

    # ------------------------------------------------------------------
    def _build_import_section(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="1. Import leads")
        frame.grid(row=0, column=0, sticky="ew")
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Source file").grid(row=0, column=0, padx=4, pady=4, sticky="w")
        ttk.Entry(frame, textvariable=self.file_var).grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        ttk.Button(frame, text="Browse", command=self.browse_file).grid(row=0, column=2, padx=4, pady=4)

        self.sample_tree = ttk.Treeview(frame, columns=("#1", "#2", "#3"), show="headings", height=5)
        self.sample_tree.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=4, pady=(8, 4))
        frame.rowconfigure(1, weight=1)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.sample_tree.yview)
        self.sample_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=1, column=3, sticky="ns")

    # ------------------------------------------------------------------
    def _build_progress_section(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="3. Verification progress")
        frame.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        frame.columnconfigure(0, weight=1)

        progress = ttk.Progressbar(frame, maximum=100, variable=self.progress_var)
        progress.grid(row=0, column=0, columnspan=3, sticky="ew", padx=4, pady=4)

        ttk.Label(frame, textvariable=self.status_var).grid(row=1, column=0, columnspan=3, sticky="w", padx=4, pady=4)

        ttk.Button(frame, text="Start", command=self.start_verification).grid(row=2, column=0, padx=4, pady=4, sticky="w")
        ttk.Button(frame, text="Cancel", command=self.cancel_verification).grid(row=2, column=1, padx=4, pady=4, sticky="w")
        ttk.Button(frame, text="Clear results", command=self.clear_results).grid(row=2, column=2, padx=4, pady=4, sticky="e")

    # ------------------------------------------------------------------
    def _build_results_section(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="4. Results")
        frame.grid(row=3, column=0, sticky="nsew", pady=(12, 0))
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        filter_bar = ttk.Frame(frame)
        filter_bar.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        filter_bar.columnconfigure(1, weight=1)

        ttk.Label(filter_bar, text="Filter").grid(row=0, column=0, padx=(0, 8))
        ttk.Entry(filter_bar, textvariable=self.filter_var).grid(row=0, column=1, sticky="ew")

        btn_bar = ttk.Frame(filter_bar)
        btn_bar.grid(row=0, column=2, padx=(8, 0))
        ttk.Button(btn_bar, text="Export CSV", command=self.export_csv).pack(side="left", padx=(0, 4))
        ttk.Button(btn_bar, text="Export Excel", command=self.export_excel).pack(side="left")

        columns = ("lead", "status", "source", "details")
        self.results_tree = ttk.Treeview(frame, columns=columns, show="headings")
        for column, heading in zip(columns, ["Lead", "Status", "Source", "Details"]):
            self.results_tree.heading(column, text=heading)
            self.results_tree.column(column, anchor="w")
        self.results_tree.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)

        scroll = ttk.Scrollbar(frame, orient="vertical", command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scroll.set)
        scroll.grid(row=1, column=1, sticky="ns")

    # ------------------------------------------------------------------
    def browse_file(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Spreadsheets", "*.csv *.xlsx *.xls"), ("CSV", "*.csv"), ("Excel", "*.xlsx *.xls"), ("All files", "*.*")])
        if not path:
            return
        try:
            rows = self.orchestrator.load_leads(path)
        except Exception as exc:  # pragma: no cover - GUI surface
            messagebox.showerror("Import failed", str(exc))
            return
        if not rows:
            messagebox.showwarning("No rows", "The selected file did not contain any leads.")
            return

        self.file_var.set(path)
        self.loaded_rows = rows
        columns = list(rows[0].keys())
        self.mapping_frame.update_options(columns)
        self._populate_sample_tree(columns, rows[:5])
        self.status_var.set(f"Loaded {len(rows)} leads")

    # ------------------------------------------------------------------
    def _populate_sample_tree(self, columns: List[str], rows: List[Dict[str, str]]) -> None:
        self.sample_tree.delete(*self.sample_tree.get_children())
        self.sample_tree["columns"] = columns[:3] if len(columns) > 3 else columns
        for column in self.sample_tree["columns"]:
            self.sample_tree.heading(column, text=column)
        for row in rows:
            values = [row.get(column, "") for column in self.sample_tree["columns"]]
            self.sample_tree.insert("", "end", values=values)

    # ------------------------------------------------------------------
    def start_verification(self) -> None:
        if not self.loaded_rows:
            messagebox.showwarning("No data", "Please import a lead file before starting verification.")
            return

        mapping = self.mapping_frame.get_mapping()
        if "name" not in mapping or not mapping["name"]:
            messagebox.showwarning("Missing mapping", "Select at least the column that represents the full name.")
            return

        if self.current_task and not self.current_task.done():
            messagebox.showinfo("Job running", "A verification job is already in progress.")
            return

        self.result_rows.clear()
        self.refresh_result_table()
        self.progress_var.set(0.0)
        self.status_var.set("Starting verification...")
        self.source_styles.clear()
        self._color_cycle = itertools.cycle(self.SOURCE_COLORS)

        total = len(self.loaded_rows)

        def progress_callback(current: int, total_rows: int) -> None:
            self.event_queue.put(("progress", current, total_rows))

        def result_callback(result: LeadVerificationResult) -> None:
            self.event_queue.put(("result", result))

        def completion_callback(results: List[LeadVerificationResult]) -> None:
            self.event_queue.put(("done", results))

        try:
            self.current_task = self.orchestrator.verify_async(
                leads=self.loaded_rows,
                mapping=mapping,
                progress_callback=progress_callback,
                result_callback=result_callback,
                completion_callback=completion_callback,
            )
        except Exception as exc:  # pragma: no cover - GUI surface
            messagebox.showerror("Verification failed", str(exc))
            self.status_var.set("Error starting verification")
            return

        if total:
            self.progress_step = 100.0 / total
        else:
            self.progress_step = 0
        self.status_var.set("Verification running...")

    # ------------------------------------------------------------------
    def cancel_verification(self) -> None:
        if self.current_task and not self.current_task.done():
            self.current_task.cancel()
            self.status_var.set("Cancellation requested")

    # ------------------------------------------------------------------
    def clear_results(self) -> None:
        self.result_rows.clear()
        self.refresh_result_table()
        self.progress_var.set(0.0)
        self.status_var.set("Results cleared")
        self.source_styles.clear()
        self._color_cycle = itertools.cycle(self.SOURCE_COLORS)

    # ------------------------------------------------------------------
    def export_csv(self) -> None:
        if not self.result_rows:
            messagebox.showinfo("No results", "Run a verification job before exporting.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not path:
            return
        try:
            export_to_csv(path, self.result_rows)
        except Exception as exc:  # pragma: no cover - GUI surface
            messagebox.showerror("Export failed", str(exc))
            return
        messagebox.showinfo("Export complete", f"Results exported to {path}")

    # ------------------------------------------------------------------
    def export_excel(self) -> None:
        if not self.result_rows:
            messagebox.showinfo("No results", "Run a verification job before exporting.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx"), ("Excel 97-2004", "*.xls")])
        if not path:
            return
        try:
            export_to_excel(path, self.result_rows)
        except Exception as exc:  # pragma: no cover - GUI surface
            messagebox.showerror("Export failed", str(exc))
            return
        messagebox.showinfo("Export complete", f"Results exported to {path}")

    # ------------------------------------------------------------------
    def _poll_queue(self) -> None:
        try:
            while True:
                event = self.event_queue.get_nowait()
                self._handle_event(event)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self._poll_queue)

    # ------------------------------------------------------------------
    def _handle_event(self, event: tuple) -> None:
        kind = event[0]
        if kind == "progress":
            _, current, total = event
            if total:
                self.progress_var.set(min(100.0, (current / total) * 100.0))
            self.status_var.set(f"Processing lead {current} of {total}")
        elif kind == "result":
            _, result = event
            self.result_rows.append(result)
            self.refresh_result_table()
        elif kind == "done":
            _, results = event
            # Ensure we capture any final results emitted directly in completion callback
            if results:
                existing_ids = {(res.lead.name, res.source, res.status, res.details) for res in self.result_rows}
                for result in results:
                    key = (result.lead.name, result.source, result.status, result.details)
                    if key not in existing_ids:
                        self.result_rows.append(result)
            self.refresh_result_table()
            self.status_var.set("Verification finished")
            self.current_task = None
            self.progress_var.set(100.0 if self.result_rows else 0.0)

    # ------------------------------------------------------------------
    def refresh_result_table(self) -> None:
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        term = self.filter_var.get().strip().lower()
        for result in self._filtered_results(term):
            tag = self._tag_for_source(result.source)
            self.results_tree.insert(
                "",
                "end",
                values=(self._format_lead(result), result.status, result.source, result.details),
                tags=(tag,),
            )

    # ------------------------------------------------------------------
    def _filtered_results(self, term: str) -> Iterable[LeadVerificationResult]:
        if not term:
            return list(self.result_rows)
        filtered: List[LeadVerificationResult] = []
        for result in self.result_rows:
            haystack = " ".join(
                filter(
                    None,
                    [
                        result.lead.name,
                        result.lead.phone or "",
                        result.lead.email or "",
                        result.source,
                        result.status,
                        result.details,
                    ],
                )
            ).lower()
            if term in haystack:
                filtered.append(result)
        return filtered

    # ------------------------------------------------------------------
    def _format_lead(self, result: LeadVerificationResult) -> str:
        parts = [result.lead.name]
        if result.lead.phone:
            parts.append(result.lead.phone)
        if result.lead.email:
            parts.append(result.lead.email)
        return " · ".join(parts)

    # ------------------------------------------------------------------
    def _tag_for_source(self, source: str) -> str:
        if source not in self.source_styles:
            style = next(self._color_cycle)
            self.source_styles[source] = style
            tag_name = f"source::{source}"
            self.results_tree.tag_configure(tag_name, background=style.background, foreground=style.foreground)
        else:
            style = self.source_styles[source]
            tag_name = f"source::{source}"
            # Ensure tag exists in case Treeview was recreated
            self.results_tree.tag_configure(tag_name, background=style.background, foreground=style.foreground)
        return tag_name

    # ------------------------------------------------------------------
    def on_close(self) -> None:
        if self.current_task and not self.current_task.done():
            if not messagebox.askyesno("Quit", "A verification job is running. Quit anyway?"):
                return
        self.orchestrator.shutdown()
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    app = LeadVerifierApp(root)
    root.mainloop()


if __name__ == "__main__":  # pragma: no cover - manual launch
    main()
