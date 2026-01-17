
# -*- coding: utf-8 -*-
# ============================================
# 🚨 必裝套件：pip install pandas tkcalendar matplotlib numpy
# ============================================

import tkinter as tk
from tkinter import messagebox, ttk
import pandas as pd
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'Arial Unicode MS', 'SimHei']
matplotlib.rcParams['axes.unicode_minus'] = False

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))

from daily_report import DailyReport
from erp_tabs import ProductionManagerGUI
from report_module import InventoryReports
# from production_gui import ProductionManagerGUI


def safe_emoji(text):
    return ''.join(c for c in text if ord(c) <= 0xFFFF)

class ERPMainUI:
    def __init__(self, root):
        self.root = root
        self.root.title("庫存小幫手")
        self.root.geometry("1000x700")
        self.root.configure(bg="white")
        self.root.iconbitmap("assets/erp_icon.ico")

        self.img_daily = tk.PhotoImage(file="assets/icon_daily.png")
        self.img_mfg = tk.PhotoImage(file="assets/icon_mfg.png")
        self.img_sales = tk.PhotoImage(file="assets/icon_sales.png")
        self.img_adjust = tk.PhotoImage(file="assets/icon_warehouse_out.png")

        self.reports = InventoryReports(self.root)

        self.setup_top_bar()
        self.setup_title()
        self.setup_main_buttons()
        self.setup_reports()
        self.setup_exit()


    def setup_top_bar(self):
        top_frame = tk.Frame(self.root, bg="white")
        top_frame.pack(fill="x", pady=(10, 0), padx=20)
        tk.Label(top_frame, text=safe_emoji("🏢 公司別："), bg="white", font=("Segoe UI", 12, "bold")).pack(side="left")
        self.company_var = tk.StringVar(value="亮晶晶公司")
        company_combo = ttk.Combobox(top_frame, textvariable=self.company_var, state="readonly", width=10)
        company_combo["values"] = ["亮晶晶公司", "閃亮亮公司"]
        company_combo.pack(side="left", padx=5)

    def setup_title(self):
        title_frame = tk.Frame(self.root, bg="white")
        title_frame.pack(pady=(0, 20))
        tk.Label(title_frame, text=safe_emoji("📦   庫存小幫手 (ง •̀_•́)ง  "), font=("Segoe UI", 20, "bold"),
                 bg="white", fg="#3E4A89").pack()

    def setup_main_buttons(self):
        self.btn_frame = tk.Frame(self.root, bg="white")
        self.btn_frame.pack(pady=(10, 15))
        btn_font = ("Noto Sans TC", 16, "bold")

        def create_icon_button(image, label, row, col, command):
            btn = tk.Button(self.btn_frame, text=label, image=image, compound="top",
                            font=btn_font, fg="black", bg="white", command=command, bd=0)
            btn.image = image
            btn.grid(row=row, column=col, padx=30, pady=20)

        create_icon_button(self.img_daily, "每日看板", 0, 1, self.open_daily_report)
        create_icon_button(self.img_sales, "訂單管理", 1, 0, lambda: self.open_gui_and_focus_tab("訂單管理"))
        create_icon_button(self.img_mfg, "生產入庫", 1, 1, lambda: self.open_gui_and_focus_tab("生產管理"))
        create_icon_button(self.img_adjust, "庫存管理", 1, 2, lambda: self.open_gui_and_focus_tab("庫存管理"))

    def setup_reports(self):
        report_names = [
            "商品庫存圖",
            "銷售客戶排名圖",
            "銷貨量排名圖",
            "銷貨金額排名圖",
            "庫存金額"
        ]

        report_funcs = [
            self.reports.show_inventory_bar_chart,
            self.reports.show_customer_value_chart,
            self.reports.show_shipment_volume_chart,
            self.reports.show_sales_amount_chart,
            self.reports.show_inventory_pie_chart
        ]

        report_frame = tk.Frame(self.root, bg="white")
        report_frame.pack(pady=10)

        for i, (name, func) in enumerate(zip(report_names, report_funcs)):
            btn = tk.Button(
                report_frame,
                text=safe_emoji(name),
                width=14,
                height=2,
                bg="#E5989B",
                fg="white",
                font=("Noto Sans TC", 12, "bold"),
                wraplength=120,
                justify="center",
                command=func
            )
            btn.grid(row=0, column=i, padx=6)

    def setup_exit(self):
        exit_btn = tk.Button(self.root, text=safe_emoji("🚪 離開"),
                             font=("Noto Sans TC", 9, "bold"), width=6,
                             command=self.root.quit, bg="#4A90E2", fg="white")
        exit_btn.place(relx=1.0, rely=1.0, anchor="se", x=-20, y=-20)

    def open_gui_and_focus_tab(self, tab_name):
        try:
            new_window = tk.Toplevel(self.root)

            try:
                new_window.iconbitmap(os.path.join("assets", "erp_icon.ico"))
            except Exception as e:
                print(f"子視窗圖示載入失敗：{e}")

            gui = ProductionManagerGUI(new_window)
            tab_map = {
                "訂單管理": 0,
                "生產管理": 1,
                "庫存管理": 2
            }
            if tab_name in tab_map:
                gui.notebook.select(tab_map[tab_name])
        except Exception as e:
            messagebox.showerror("錯誤", f"無法開啟畫面：\n{str(e)}")


    def open_daily_report(self):
        try:
            report_window = tk.Toplevel(self.root)
            DailyReport(report_window)
        except Exception as e:
            messagebox.showerror("錯誤", f"無法開啟每日看板畫面：\n{str(e)}")

    # def load_data(self):
    #     return pd.read_excel("訂單測試資料.xlsx", sheet_name="Sheet1")


if __name__ == "__main__":
    root = tk.Tk()
    app = ERPMainUI(root)
    root.mainloop()
