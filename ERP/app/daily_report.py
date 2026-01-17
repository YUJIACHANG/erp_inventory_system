#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import date, datetime
import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import matplotlib
# 字型設定：用微軟正黑體或 Noto Sans TC，防止中文亂碼
matplotlib.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'Noto Sans TC']
matplotlib.rcParams['axes.unicode_minus'] = False
import os
import re
import json

matplotlib.use("TkAgg")


class DailyReport:
    def __init__(self, root):
        self.root = root
        self.root.title("每日看板")
        self.root.geometry("1000x700")
        self.root.configure(bg="white")
        self.root.iconbitmap("assets/erp_icon.ico")
        self.is_fullscreen = False

        self.load_sample_data()
        self.create_filters()
        self.create_stats_section()
        self.create_charts()
        self.create_update_time_label()
        self.configure_styles()
        self.filter_data()
        self.schedule_auto_refresh()

    def configure_styles(self):
        default_font = ("Noto Sans TC")
        self.root.option_add("*Font", default_font)  # 全域套用字型
        style = ttk.Style()
        style.configure("TButton", padding=5)
        style.configure("TLabel", font=default_font)
        style.configure("TCombobox", font=default_font)

    def load_sample_data(self):
        # 載入 JSON 檔案資料
        json_path = r"working_data/orders_data.json"
        if not os.path.exists(json_path):
            messagebox.showerror("檔案錯誤", f"找不到檔案：{json_path}\n請確認檔案路徑與名稱正確")
            self.root.destroy()
            return

        with open(json_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        orders = json_data.get("orders", [])

        # 將訂單資料轉為 DataFrame
        df = pd.DataFrame(orders)

        # 確認所有必要欄位存在，缺少則補 None
        required_cols = ["date", "status", "quantity", "price", "prod_id", "prod_name", "cust_id", "cust_name"]
        for col in required_cols:
            if col not in df.columns:
                df[col] = None

        # 重新命名欄位以符合程式使用
        df.rename(columns={
            "date": "日期",
            "status": "狀態",
            "quantity": "訂購數量",
            "price": "單價",
            "prod_id": "品號",
            "prod_name": "品名",
            "cust_id": "客戶代號",
            "cust_name": "客戶名稱",
        }, inplace=True)

        # 計算金額欄位 = 訂購數量 * 單價
        df["金額"] = df["訂購數量"] * df["單價"]

        # 將日期字串轉換為 datetime 物件
        df["日期"] = pd.to_datetime(df["日期"])

        # 設定送出碼，狀態為"已出貨"為 Y，其餘 N
        df["送出碼"] = df["狀態"].apply(lambda x: "Y" if x in ["已出貨"] else "N")

        # 進出別對應，已出貨或已分配為出庫，新訂單為入庫，其他為其他
        def map_inout(status):
            if status in ["已出貨", "已分配"]:
                return "出庫"
            elif status == "新訂單":
                return "入庫"
            else:
                return "其他"
        df["進出別"] = df["狀態"].map(map_inout)

        # 將客戶代號轉成字串，方便後續組合顯示
        df["客戶代號"] = df["客戶代號"].astype(str)
        df["客戶/供應商"] = df["客戶代號"] + " " + df["客戶名稱"].astype(str)

        # 從品號中提取數字，用於排序
        def extract_number(p):
            match = re.search(r'\d+', str(p))
            return int(match.group()) if match else 0

        df['品號號碼'] = df['品號'].apply(extract_number)

        # 取得排序後的品號清單，供過濾下拉選單使用
        unique_products = df['品號'].dropna().unique()
        product_list = sorted(unique_products, key=lambda x: str(x))  # 轉字串再排序，避免出錯

        self.product_categories = ["全部"] + product_list
        self.data = df

    def configure_styles(self):
        # 設定按鈕字型與邊距
        style = ttk.Style()
        style.configure('TButton', font=('Arial', 10), padding=5)

    def create_filters(self):
        filter_frame = tk.Frame(self.root, bg="white")
        filter_frame.pack(fill="x", padx=20, pady=(20, 10))

        # 品類選擇下拉
        tk.Label(filter_frame, text="品類", bg="white", font=("Arial", 12)).pack(side="left")
        self.category_var = tk.StringVar()
        self.category_combobox = ttk.Combobox(filter_frame, textvariable=self.category_var, state="readonly", width=10)
        self.category_combobox["values"] = self.product_categories
        self.category_combobox.current(0)
        self.category_combobox.pack(side="left", padx=(5, 20))
        self.category_combobox.bind("<<ComboboxSelected>>", self.filter_data)

        # 日期選擇器
        tk.Label(filter_frame, text="選擇日期", bg="white", font=("Arial", 12)).pack(side="left")
        self.date_var = tk.StringVar()
        self.date_entry = DateEntry(filter_frame, width=12, background='darkblue',
                                    foreground='white', borderwidth=2,
                                    date_pattern='yyyy-mm-dd', textvariable=self.date_var, showweeknumbers=False)
        self.date_entry.pack(side="left", padx=(5, 20))

        # 查詢按鈕
        self.search_button = ttk.Button(filter_frame, text="查詢", command=self.filter_data)
        self.search_button.pack(side="left", padx=(5, 20))

        # 更新資料按鈕
        self.import_button = ttk.Button(filter_frame, text="更新資料", command=self.manual_refresh)
        self.import_button.pack(side="right")

        # 全螢幕切換按鈕
        self.fullscreen_button = ttk.Button(filter_frame, text="全螢幕", command=self.toggle_fullscreen)
        self.fullscreen_button.pack(side="right", padx=(10, 10))

    def toggle_fullscreen(self):
        # 切換全螢幕狀態
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes("-fullscreen", self.is_fullscreen)
        self.fullscreen_button.config(text="縮回視窗" if self.is_fullscreen else "全螢幕")

    def manual_refresh(self):
        # 手動重新載入資料並過濾
        self.load_sample_data()
        self.filter_data()

    def create_stats_section(self):
        # 建立顯示統計資料的區塊
        self.stats_frame = tk.Frame(self.root, bg="white")
        self.stats_frame.pack(fill="both", expand=False, padx=20, pady=(0, 20))
        self.stats_frame.columnconfigure((0, 1), weight=1)

    def create_charts(self):
        # 建立圖表顯示區域
        self.charts_frame = tk.Frame(self.root, bg="white")
        self.charts_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.chart_frame1 = tk.Frame(self.charts_frame, bg="white")
        self.chart_frame1.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        tk.Label(self.chart_frame1, text="每日出貨產品數量佔比", bg="white", font=("Arial", 12, "bold")).pack()

        self.chart_frame2 = tk.Frame(self.charts_frame, bg="white")
        self.chart_frame2.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        tk.Label(self.chart_frame2, text="每日出貨品號金額分析", bg="white", font=("Arial", 12, "bold")).pack()

        self.charts_frame.columnconfigure((0, 1), weight=1)
        self.charts_frame.rowconfigure(0, weight=1)

    def create_update_time_label(self):
        # 建立顯示最後更新時間的標籤
        self.update_label = tk.Label(self.root, text="", bg="white", font=("Arial", 10, "italic"), anchor="e")
        self.update_label.pack(fill="x", padx=20, pady=(0, 5))

    def update_last_updated_time(self):
        # 更新顯示最後更新時間文字
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.update_label.config(text=f"最後更新時間：{now_str}")

    def filter_data(self, event=None):
        # 根據選擇的品類和日期過濾資料
        selected_category = self.category_var.get()
        try:
            selected_date = self.date_entry.get_date()
        except Exception:
            selected_date = date.today()
            self.date_entry.set_date(selected_date)

        shipped_data = self.data[self.data["送出碼"] == "Y"]  # 只取已出貨
        date_filtered_data = shipped_data[shipped_data["日期"].dt.date == selected_date]

        if selected_category != "全部":
            filtered_data = date_filtered_data[date_filtered_data["品號"] == selected_category]
        else:
            filtered_data = date_filtered_data

        self.update_stats(filtered_data)
        self.update_charts(filtered_data)
        self.update_last_updated_time()

    def update_stats(self, filtered_data):
        # 更新統計區塊內容
        for widget in self.stats_frame.winfo_children():
            widget.destroy()

        stats = [
            ("當天出貨數量", filtered_data["訂購數量"].sum(), "#039BE5"),
            ("當天出貨金額", f"{filtered_data['金額'].sum():,.0f}", "#F57C00")
        ]

        for i, (label, value, color) in enumerate(stats):
            frame = tk.Frame(self.stats_frame, bg=color, width=200, height=80)
            frame.grid(row=0, column=i, padx=10, pady=10, sticky="nsew")
            frame.pack_propagate(False)
            tk.Label(frame, text=label, bg=color, fg="white", font=("Arial", 12)).pack(pady=(10, 0))
            tk.Label(frame, text=value, bg=color, fg="white", font=("Arial", 20, "bold")).pack(pady=(5, 10))

    def update_charts(self, filtered_data):
        # 更新圖表內容
        # rcParams['font.sans-serif'] = ['PingFang TC', 'Arial Unicode MS', 'sans-serif']
        rcParams['axes.unicode_minus'] = False

        # 清除先前圖表物件
        for frame in [self.chart_frame1, self.chart_frame2]:
            for widget in frame.winfo_children()[1:]:
                widget.destroy()

        if filtered_data.empty:
            for frame in [self.chart_frame1, self.chart_frame2]:
                tk.Label(frame, text="沒有符合條件的數據", bg="white", font=("Arial", 12)).pack(expand=True)
            return

        # 圓餅圖：每日出貨產品數量佔比
        fig1 = plt.Figure(figsize=(4, 3), dpi=100)
        ax1 = fig1.add_subplot(111)
        qty_by_product = filtered_data.groupby("品名")["訂購數量"].sum()
        colors_pie = ['#AED6F1', '#5DADE2', '#2874A6', '#1B4F72']
        qty_by_product.plot(kind="pie", autopct='%1.1f%%', ax=ax1, ylabel="", colors=colors_pie)
        canvas1 = FigureCanvasTkAgg(fig1, master=self.chart_frame1)
        canvas1.get_tk_widget().pack(fill="both", expand=True)

        # 長條圖：每日出貨品號金額分析
        fig2 = plt.Figure(figsize=(4, 3), dpi=100)
        fig2.subplots_adjust(left=0.25)
        ax2 = fig2.add_subplot(111)
        amount_by_product = filtered_data.groupby("品號")["金額"].sum()
        品號品名_map = filtered_data.drop_duplicates(subset=["品號"]).set_index("品號")["品名"].to_dict()
        labels = [f"{prod}{品號品名_map.get(prod, '')}" for prod in amount_by_product.index]
        amount_by_product.plot(kind="bar", ax=ax2, color="#FFCC80")
        ax2.set_ylabel("金\n額", rotation=360)
        ax2.set_title("")
        ax2.set_xlabel("品號與品名")
        ax2.set_xticks(range(len(labels)))
        ax2.set_xticklabels(labels, rotation=0, ha='center')
        canvas2 = FigureCanvasTkAgg(fig2, master=self.chart_frame2)
        canvas2.get_tk_widget().pack(fill="both", expand=True)

    def schedule_auto_refresh(self):
        # 每10分鐘自動重新載入資料與更新
        self.load_sample_data()
        self.filter_data()
        self.root.after(600000, self.schedule_auto_refresh)


if __name__ == "__main__":
    root = tk.Tk()
    app = DailyReport(root)
    root.mainloop()