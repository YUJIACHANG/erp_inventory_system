
import tkinter as tk
from tkinter import ttk

class SalesEntryWindow:
    def __init__(self, master):
        self.master = master
        self.master.title("銷貨單建立作業")
        self.master.geometry("1024x600")
        self.master.configure(bg="white")

        self.create_form()
        self.create_detail()
        self.create_summary()
        self.create_buttons()

    def create_form(self):
        form_frame = tk.Frame(self.master, bg="white")
        form_frame.pack(pady=10, padx=20, fill="x")

        fields = [
            ("銷貨單別", "210"),
            ("銷貨單號", "20083000001"),
            ("單據日期", "2020/08/30"),
            ("客戶代碼", "1101"),
            ("客戶名稱", "大同家具"),
        ]

        for i, (label, default) in enumerate(fields):
            tk.Label(form_frame, text=label, bg="white", anchor="w", width=12).grid(row=i, column=0, sticky="w", pady=2)
            entry = tk.Entry(form_frame, width=30)
            entry.insert(0, default)
            entry.grid(row=i, column=1, padx=10, pady=2)

    def create_detail(self):
        detail_frame = tk.LabelFrame(self.master, text="商品明細", bg="white")
        detail_frame.pack(padx=20, pady=10, fill="both", expand=True)

        self.tree = ttk.Treeview(detail_frame, columns=("品號", "品名", "數量", "單價", "單位"), show="headings", height=6)
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)

        for col in ("品號", "品名", "數量", "單價", "單位"):
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center")

        self.tree.insert("", "end", values=("111001", "主機組合成品", "2", "480", "SET"))

    def create_summary(self):
        total_frame = tk.Frame(self.master, bg="white")
        total_frame.pack(pady=5, padx=20, anchor="e")

        tk.Label(total_frame, text="銷貨金額：", bg="white").grid(row=0, column=0, sticky="e")
        total_entry = tk.Entry(total_frame, width=12, justify="right")
        total_entry.insert(0, "960")
        total_entry.grid(row=0, column=1)

        tk.Label(total_frame, text="總數量：", bg="white").grid(row=0, column=2, sticky="e", padx=(20, 0))
        qty_entry = tk.Entry(total_frame, width=12, justify="right")
        qty_entry.insert(0, "2")
        qty_entry.grid(row=0, column=3)

    def create_buttons(self):
        btn_frame = tk.Frame(self.master, bg="white")
        btn_frame.pack(pady=15)

        for name in ["新增", "刪除", "儲存", "取消", "列印"]:
            tk.Button(btn_frame, text=name, width=10).pack(side="left", padx=8)
