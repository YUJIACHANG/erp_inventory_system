#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox
import json
import pandas as pd
from datetime import datetime, date, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
import numpy as np

# 設定中文字體
matplotlib.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False
matplotlib.use("TkAgg")


class InventoryReports:
    def __init__(self, root):
        self.root = root
        self.data_file = "working_data/inventory_data.json"
        self.load_data()

    def load_data(self):
        """從JSON文件載入庫存數據"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.products = data.get('products', {})
            self.transactions = data.get('transactions', [])

            # 轉換交易數據為DataFrame
            if self.transactions:
                self.df_transactions = pd.DataFrame(self.transactions)
                self.df_transactions['Timestamp'] = pd.to_datetime(self.df_transactions['Timestamp'])
            else:
                self.df_transactions = pd.DataFrame()

        except FileNotFoundError:
            messagebox.showwarning("尚未開帳", "找不到庫存資料檔案（working_data/inventory_data.json）。\n請先匯入初始資料或進行開帳。")
            self.products = {}
            self.transactions = []
            self.df_transactions = pd.DataFrame()
        except Exception as e:
            messagebox.showerror("載入錯誤", f"無法載入庫存資料：{str(e)}")
            self.products = {}
            self.transactions = []
            self.df_transactions = pd.DataFrame()

    def get_available_dates(self):
        """獲取可用的日期列表"""
        dates = set()

        # 從產品創建日期獲取
        for product_info in self.products.values():
            created_date = product_info.get('created_date', '')
            if created_date:
                try:
                    date_obj = datetime.fromisoformat(created_date).date()
                    dates.add(date_obj)
                except:
                    continue

        # 從交易記錄獲取
        if not self.df_transactions.empty:
            transaction_dates = self.df_transactions['Timestamp'].dt.date.unique()
            dates.update(transaction_dates)

        # 如果沒有日期，至少提供今天
        if not dates:
            dates.add(date.today())

        # 轉換為字符串列表並排序
        date_strings = [d.strftime("%Y-%m-%d") for d in sorted(dates, reverse=True)]
        return date_strings

    def create_filter_window(self, title, callback, filter_type="full"):
        """創建包含篩選器的通用窗口
        filter_type: "full" (完整日期範圍), "end_only" (僅結束日期), "date_dropdown" (日期下拉選單)
        """
        filter_window = tk.Toplevel(self.root)
        filter_window.title(title)
        filter_window.geometry("1000x700")
        try:
            filter_window.iconbitmap("assets/erp_icon.ico")
        except Exception as e:
            print(f"載入圖示失敗: {e}")

        # 篩選器框架
        filter_frame = tk.Frame(filter_window, bg="lightgray", height=80)
        filter_frame.pack(fill="x", padx=10, pady=5)
        filter_frame.pack_propagate(False)

        # 日期篩選
        date_frame = tk.Frame(filter_frame, bg="lightgray")
        date_frame.pack(side="left", padx=10, pady=10)

        if filter_type == "date_dropdown":
            tk.Label(date_frame, text="選擇日期:", bg="lightgray", font=("Arial", 10, "bold")).pack(anchor="w")

            date_controls = tk.Frame(date_frame, bg="lightgray")
            date_controls.pack()

            # 設定虛擬的開始日期變數
            start_date_var = tk.StringVar(value="2000-01-01")

            # 日期下拉選單 - 允許手動輸入
            available_dates = self.get_available_dates()
            end_date_var = tk.StringVar(
                value=available_dates[0] if available_dates else datetime.now().strftime("%Y-%m-%d"))

            tk.Label(date_controls, text="日期:", bg="lightgray").pack(side="left")
            date_combo = ttk.Combobox(date_controls, textvariable=end_date_var,
                                      values=available_dates, width=15)  # 移除 state="readonly"，增加寬度
            date_combo.pack(side="left", padx=2)

            # 添加日期格式提示
            tk.Label(date_controls, text="(YYYY-MM-DD)", bg="lightgray",
                     font=("Arial", 8), fg="gray").pack(side="left", padx=(2, 0))

        elif filter_type == "end_only":
            tk.Label(date_frame, text="截止日期:", bg="lightgray", font=("Arial", 10, "bold")).pack(anchor="w")

            date_controls = tk.Frame(date_frame, bg="lightgray")
            date_controls.pack()

            # 只顯示結束日期
            start_date_var = tk.StringVar(value="2000-01-01")  # 設定一個很早的開始日期

            tk.Label(date_controls, text="截止到:", bg="lightgray").pack(side="left")
            end_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
            end_date_entry = tk.Entry(date_controls, textvariable=end_date_var, width=12)
            end_date_entry.pack(side="left", padx=2)
        else:
            tk.Label(date_frame, text="日期範圍:", bg="lightgray", font=("Arial", 10, "bold")).pack(anchor="w")

            date_controls = tk.Frame(date_frame, bg="lightgray")
            date_controls.pack()

            tk.Label(date_controls, text="從:", bg="lightgray").pack(side="left")
            start_date_var = tk.StringVar(value=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"))
            start_date_entry = tk.Entry(date_controls, textvariable=start_date_var, width=12)
            start_date_entry.pack(side="left", padx=2)

            tk.Label(date_controls, text="到:", bg="lightgray").pack(side="left", padx=(10, 0))
            end_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
            end_date_entry = tk.Entry(date_controls, textvariable=end_date_var, width=12)
            end_date_entry.pack(side="left", padx=2)

        # 產品篩選
        product_frame = tk.Frame(filter_frame, bg="lightgray")
        product_frame.pack(side="left", padx=20, pady=10)

        tk.Label(product_frame, text="產品篩選:", bg="lightgray", font=("Arial", 10, "bold")).pack(anchor="w")

        product_controls = tk.Frame(product_frame, bg="lightgray")
        product_controls.pack()

        tk.Label(product_controls, text="產品ID:", bg="lightgray").pack(side="left")
        product_var = tk.StringVar()

        # 創建產品ID下拉選單
        product_ids = list(
            set([info.get('product_id', '') for info in self.products.values() if info.get('product_id')]))
        product_ids.sort()
        product_combo = ttk.Combobox(product_controls, textvariable=product_var,
                                     values=['全部'] + product_ids, width=15)
        product_combo.set('全部')
        product_combo.pack(side="left", padx=2)

        # 重設按鈕放在產品篩選的右邊
        reset_btn = tk.Button(product_controls, text="重設",
                              command=lambda: self.reset_filters(start_date_var, end_date_var, product_var,
                                                                 filter_type),
                              bg="#FF9800", fg="white", font=("Arial", 10, "bold"), width=8)
        reset_btn.pack(side="left", padx=(10, 0))

        # 按鈕框架（現在只有兩個按鈕）
        button_frame = tk.Frame(filter_frame, bg="lightgray")
        button_frame.pack(side="right", padx=10, pady=10)

        # 設定統一的按鈕樣式參數
        button_width = 12
        button_font = ("Arial", 10, "bold")

        # 重新載入資料按鈕 (放在最左邊)
        reload_btn = tk.Button(button_frame, text="重新載入資料",
                               command=lambda: self.reload_and_refresh(filter_window, callback,
                                                                       start_date_var, end_date_var, product_var),
                               bg="#2196F3", fg="white", font=button_font, width=button_width)
        reload_btn.pack(side="top")

        apply_btn = tk.Button(button_frame, text="套用篩選",
                              command=lambda: callback(filter_window, start_date_var.get(),
                                                       end_date_var.get(), product_var.get()),
                              bg="#4CAF50", fg="white", font=button_font, width=button_width)
        apply_btn.pack(side="top", pady=(5, 0))

        # 圖表區域
        chart_frame = tk.Frame(filter_window)
        chart_frame.pack(fill="both", expand=True, padx=10, pady=5)

        return filter_window, chart_frame

    def reload_and_refresh(self, window, callback, start_date_var, end_date_var, product_var):
        """重新載入資料並重整圖表"""
        try:
            # 重新載入 JSON 資料
            self.load_data()

            # 顯示載入成功訊息
            messagebox.showinfo("成功", "資料已重新載入！")

            # 重新生成圖表
            callback(window, start_date_var.get(), end_date_var.get(), product_var.get())

        except Exception as e:
            messagebox.showerror("錯誤", f"重新載入資料失敗: {str(e)}")

    def reset_filters(self, start_date_var, end_date_var, product_var, filter_type="full"):
        """重設篩選器"""
        if filter_type == "date_dropdown":
            available_dates = self.get_available_dates()
            start_date_var.set("2000-01-01")
            end_date_var.set(available_dates[0] if available_dates else datetime.now().strftime("%Y-%m-%d"))
        elif filter_type == "end_only":
            start_date_var.set("2000-01-01")
            end_date_var.set(datetime.now().strftime("%Y-%m-%d"))
        else:
            start_date_var.set((datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"))
            end_date_var.set(datetime.now().strftime("%Y-%m-%d"))
        product_var.set('全部')

    def filter_products_by_criteria(self, start_date, end_date, product_id):
        """根據條件篩選產品"""
        try:
            # 驗證日期格式
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)  # 包含結束日期
            except ValueError:
                messagebox.showerror("錯誤", f"日期格式不正確，請使用 YYYY-MM-DD 格式\n例如：2025-05-20")
                return {}

            filtered_products = {}

            for product_name, product_info in self.products.items():
                # 檢查創建日期
                created_date = datetime.fromisoformat(product_info.get('created_date', ''))
                if not (start_dt <= created_date < end_dt):
                    continue

                # 檢查產品ID
                if product_id != '全部' and product_info.get('product_id', '') != product_id:
                    continue

                filtered_products[product_name] = product_info

            return filtered_products

        except Exception as e:
            messagebox.showerror("錯誤", f"篩選條件錯誤: {str(e)}")
            return {}

    def show_inventory_bar_chart(self):
        """顯示庫存條形圖 - 使用日期下拉選單"""

        def generate_chart(window, start_date, end_date, product_id):
            # 清除現有圖表
            for widget in chart_frame.winfo_children():
                widget.destroy()

            filtered_products = self.filter_products_by_criteria(start_date, end_date, product_id)

            if not filtered_products:
                tk.Label(chart_frame, text="沒有符合條件的數據", font=("Arial", 14)).pack(expand=True)
                return

            # 準備數據
            product_names = []
            quantities = []

            for product_name, product_info in filtered_products.items():
                product_names.append(product_name[:15] + '...' if len(product_name) > 15 else product_name)
                quantities.append(product_info['quantity'])

            # 取前20個產品
            if len(product_names) > 20:
                sorted_data = sorted(zip(product_names, quantities), key=lambda x: x[1], reverse=True)
                product_names, quantities = zip(*sorted_data[:20])

            # 創建圖表
            fig = plt.Figure(figsize=(12, 8), dpi=100)
            ax = fig.add_subplot(111)

            bars = ax.bar(range(len(product_names)), quantities, color='skyblue', alpha=0.8)
            ax.set_title(f'商品庫存數量統計 (日期: {end_date})', fontsize=16, fontweight='bold')
            ax.set_xlabel('產品名稱', fontsize=12)
            ax.set_ylabel('庫存數量', fontsize=12)
            ax.set_xticks(range(len(product_names)))
            ax.set_xticklabels(product_names, rotation=45, ha='right')

            # 添加數值標籤
            for bar, qty in zip(bars, quantities):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width() / 2., height + 5,
                        f'{qty}', ha='center', va='bottom')

            fig.tight_layout()

            # 嵌入到tkinter窗口
            canvas = FigureCanvasTkAgg(fig, chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        window, chart_frame = self.create_filter_window("商品庫存圖", generate_chart, filter_type="date_dropdown")
        # 初始載入
        available_dates = self.get_available_dates()
        initial_date = available_dates[0] if available_dates else datetime.now().strftime("%Y-%m-%d")
        generate_chart(window, "2000-01-01", initial_date, '全部')

    def show_customer_value_chart(self):
        """顯示銷售客戶排名圖 - 只顯示已出貨訂單"""

        def generate_chart(window, start_date, end_date, product_id):
            for widget in chart_frame.winfo_children():
                widget.destroy()

            # 載入訂單資料
            try:
                import json
                with open('working_data/orders_data.json', 'r', encoding='utf-8') as f:
                    orders_data = json.load(f)
                orders = orders_data.get('orders', [])
            except FileNotFoundError:
                tk.Label(chart_frame, text="找不到訂單資料檔案", font=("Arial", 14)).pack(expand=True)
                return
            except Exception as e:
                tk.Label(chart_frame, text=f"讀取訂單資料失敗: {str(e)}", font=("Arial", 14)).pack(expand=True)
                return

            # 篩選已出貨訂單
            shipped_orders = [order for order in orders if order.get('status') == '已出貨']

            if not shipped_orders:
                tk.Label(chart_frame, text="沒有已出貨的訂單資料", font=("Arial", 14)).pack(expand=True)
                return

            # 根據日期範圍篩選
            filtered_orders = []
            for order in shipped_orders:
                order_date = order.get('date', '')
                if start_date <= order_date <= end_date:
                    # 如果指定了特定產品，則只篩選該產品
                    if product_id == '全部' or order.get('prod_id') == product_id:
                        filtered_orders.append(order)

            if not filtered_orders:
                tk.Label(chart_frame, text="沒有符合條件的已出貨訂單", font=("Arial", 14)).pack(expand=True)
                return

            # 計算客戶銷售金額
            customer_sales = {}
            for order in filtered_orders:
                customer_name = order.get('cust_name', '未知客戶')
                quantity = order.get('quantity', 0)
                price = order.get('price', 0)
                amount = quantity * price

                if customer_name not in customer_sales:
                    customer_sales[customer_name] = 0
                customer_sales[customer_name] += amount

            if not customer_sales:
                tk.Label(chart_frame, text="沒有符合條件的銷售數據", font=("Arial", 14)).pack(expand=True)
                return

            # 排序並取前10名
            sorted_customers = sorted(customer_sales.items(), key=lambda x: x[1], reverse=True)[:10]
            customers, values = zip(*sorted_customers)

            fig = plt.Figure(figsize=(10, 6), dpi=100)
            ax = fig.add_subplot(111)

            bars = ax.barh(customers, values, color='lightcoral', alpha=0.8)
            ax.set_title(f'客戶銷售金額排名 ({start_date} 至 {end_date}) - 僅已出貨訂單', fontsize=16,
                         fontweight='bold')
            ax.set_xlabel('銷售金額', fontsize=12)
            ax.set_ylabel('客戶名稱', fontsize=12)

            for bar, value in zip(bars, values):
                width = bar.get_width()
                ax.text(width + max(values) * 0.01, bar.get_y() + bar.get_height() / 2,
                        f'{value:,.0f}', ha='left', va='center')

            fig.tight_layout()
            canvas = FigureCanvasTkAgg(fig, chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        window, chart_frame = self.create_filter_window("銷售客戶排名圖", generate_chart)
        generate_chart(window, (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                       datetime.now().strftime("%Y-%m-%d"), '全部')

    def show_shipment_volume_chart(self):
        """顯示銷貨量排名圖 - 只顯示已出貨訂單"""

        def generate_chart(window, start_date, end_date, product_id):
            for widget in chart_frame.winfo_children():
                widget.destroy()

            # 載入訂單資料
            try:
                import json
                with open('working_data/orders_data.json', 'r', encoding='utf-8') as f:
                    orders_data = json.load(f)
                orders = orders_data.get('orders', [])
            except FileNotFoundError:
                tk.Label(chart_frame, text="找不到訂單資料檔案", font=("Arial", 14)).pack(expand=True)
                return
            except Exception as e:
                tk.Label(chart_frame, text=f"讀取訂單資料失敗: {str(e)}", font=("Arial", 14)).pack(expand=True)
                return

            # 篩選已出貨訂單
            shipped_orders = [order for order in orders if order.get('status') == '已出貨']

            if not shipped_orders:
                tk.Label(chart_frame, text="沒有已出貨的訂單資料", font=("Arial", 14)).pack(expand=True)
                return

            # 根據日期範圍篩選
            filtered_orders = []
            for order in shipped_orders:
                order_date = order.get('date', '')
                if start_date <= order_date <= end_date:
                    # 如果指定了特定產品，則只篩選該產品
                    if product_id == '全部' or order.get('prod_id') == product_id:
                        filtered_orders.append(order)

            if not filtered_orders:
                tk.Label(chart_frame, text="沒有符合條件的已出貨訂單", font=("Arial", 14)).pack(expand=True)
                return

            # 計算產品銷貨量
            product_volumes = {}
            for order in filtered_orders:
                product_name = order.get('prod_name', '未知產品')
                quantity = order.get('quantity', 0)

                if product_name not in product_volumes:
                    product_volumes[product_name] = 0
                product_volumes[product_name] += quantity

            if not product_volumes:
                tk.Label(chart_frame, text="沒有符合條件的銷貨數據", font=("Arial", 14)).pack(expand=True)
                return

            # 排序並取前15名
            sorted_products = sorted(product_volumes.items(), key=lambda x: x[1], reverse=True)[:15]
            product_names, shipped_quantities = zip(*sorted_products)

            # 截斷過長的產品名稱
            truncated_names = [name[:20] + '...' if len(name) > 20 else name for name in product_names]

            fig = plt.Figure(figsize=(12, 8), dpi=100)
            ax = fig.add_subplot(111)

            bars = ax.bar(range(len(truncated_names)), shipped_quantities, color='lightgreen', alpha=0.8)
            ax.set_title(f'產品銷貨量排名 ({start_date} 至 {end_date}) - 僅已出貨訂單', fontsize=16, fontweight='bold')
            ax.set_xlabel('產品名稱', fontsize=12)
            ax.set_ylabel('銷貨量', fontsize=12)
            ax.set_xticks(range(len(truncated_names)))
            ax.set_xticklabels(truncated_names, rotation=45, ha='right')

            for bar, qty in zip(bars, shipped_quantities):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width() / 2., height + max(shipped_quantities) * 0.01,
                        f'{qty}', ha='center', va='bottom')

            fig.tight_layout()
            canvas = FigureCanvasTkAgg(fig, chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        window, chart_frame = self.create_filter_window("銷貨量排名圖", generate_chart)
        generate_chart(window, (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                       datetime.now().strftime("%Y-%m-%d"), '全部')

    def show_sales_amount_chart(self):
        """顯示銷貨金額排名圖 - 只顯示已出貨訂單"""

        def generate_chart(window, start_date, end_date, product_id):
            for widget in chart_frame.winfo_children():
                widget.destroy()

            # 載入訂單資料
            try:
                import json
                with open('working_data/orders_data.json', 'r', encoding='utf-8') as f:
                    orders_data = json.load(f)
                orders = orders_data.get('orders', [])
            except FileNotFoundError:
                tk.Label(chart_frame, text="找不到訂單資料檔案", font=("Arial", 14)).pack(expand=True)
                return
            except Exception as e:
                tk.Label(chart_frame, text=f"讀取訂單資料失敗: {str(e)}", font=("Arial", 14)).pack(expand=True)
                return

            # 篩選已出貨訂單
            shipped_orders = [order for order in orders if order.get('status') == '已出貨']

            if not shipped_orders:
                tk.Label(chart_frame, text="沒有已出貨的訂單資料", font=("Arial", 14)).pack(expand=True)
                return

            # 根據日期範圍篩選
            filtered_orders = []
            for order in shipped_orders:
                order_date = order.get('date', '')
                if start_date <= order_date <= end_date:
                    # 如果指定了特定產品，則只篩選該產品
                    if product_id == '全部' or order.get('prod_id') == product_id:
                        filtered_orders.append(order)

            if not filtered_orders:
                tk.Label(chart_frame, text="沒有符合條件的已出貨訂單", font=("Arial", 14)).pack(expand=True)
                return

            # 計算產品銷貨金額
            product_amounts = {}
            for order in filtered_orders:
                product_name = order.get('prod_name', '未知產品')
                quantity = order.get('quantity', 0)
                price = order.get('price', 0)
                amount = quantity * price

                if product_name not in product_amounts:
                    product_amounts[product_name] = 0
                product_amounts[product_name] += amount

            if not product_amounts:
                tk.Label(chart_frame, text="沒有符合條件的銷貨金額數據", font=("Arial", 14)).pack(expand=True)
                return

            # 排序並取前15名
            sorted_products = sorted(product_amounts.items(), key=lambda x: x[1], reverse=True)[:15]
            product_names, amounts = zip(*sorted_products)

            # 截斷過長的產品名稱
            truncated_names = [name[:20] + '...' if len(name) > 20 else name for name in product_names]

            fig = plt.Figure(figsize=(12, 8), dpi=100)
            ax = fig.add_subplot(111)

            bars = ax.bar(range(len(truncated_names)), amounts, color='gold', alpha=0.8)
            ax.set_title(f'產品銷貨金額排名 ({start_date} 至 {end_date}) - 僅已出貨訂單', fontsize=16,
                         fontweight='bold')
            ax.set_xlabel('產品名稱', fontsize=12)
            ax.set_ylabel('銷貨金額 (元)', fontsize=12)
            ax.set_xticks(range(len(truncated_names)))
            ax.set_xticklabels(truncated_names, rotation=45, ha='right')

            for bar, amount in zip(bars, amounts):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width() / 2., height + max(amounts) * 0.01,
                        f'{amount:,.0f}', ha='center', va='bottom', fontsize=8)

            fig.tight_layout()
            canvas = FigureCanvasTkAgg(fig, chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        window, chart_frame = self.create_filter_window("銷貨金額排名圖", generate_chart)
        generate_chart(window, (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                       datetime.now().strftime("%Y-%m-%d"), '全部')
    def show_inventory_pie_chart(self):
        """顯示庫存金額圓餅圖 - 使用日期下拉選單"""

        def generate_chart(window, start_date, end_date, product_id):
            # 清除現有圖表
            for widget in chart_frame.winfo_children():
                widget.destroy()

            filtered_products = self.filter_products_by_criteria(start_date, end_date, product_id)

            if not filtered_products:
                tk.Label(chart_frame, text="沒有符合條件的數據", font=("Arial", 14)).pack(expand=True)
                return

            # 準備數據 - 按產品類別分組
            category_values = {}

            for product_name, product_info in filtered_products.items():
                # 根據產品名稱分類
                if 'LED' in product_name:
                    category = 'LED燈具'
                elif '手電筒' in product_name:
                    category = '手電筒'
                elif '投光燈' in product_name or '街燈' in product_name:
                    category = '戶外照明'
                elif '檯燈' in product_name:
                    category = '檯燈'
                elif '吸頂燈' in product_name or '吊燈' in product_name:
                    category = '室內燈具'
                else:
                    category = '其他'

                value = product_info['quantity'] * product_info.get('cost', 0)
                category_values[category] = category_values.get(category, 0) + value

            # 過濾掉值為0的類別
            category_values = {k: v for k, v in category_values.items() if v > 0}

            if not category_values:
                tk.Label(chart_frame, text="暫無庫存金額數據", font=("Arial", 14)).pack(expand=True)
                return

            categories = list(category_values.keys())
            values = list(category_values.values())

            # 創建圓餅圖
            fig = plt.Figure(figsize=(10, 8), dpi=100)
            ax = fig.add_subplot(111)

            colors = plt.cm.Set3(np.linspace(0, 1, len(categories)))
            wedges, texts, autotexts = ax.pie(values, labels=categories, autopct='%1.1f%%',
                                              startangle=90, colors=colors)

            ax.set_title(f'庫存金額分布 (日期: {end_date})', fontsize=16, fontweight='bold')

            # 美化文字
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')

            fig.tight_layout()

            canvas = FigureCanvasTkAgg(fig, chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        window, chart_frame = self.create_filter_window("庫存金額分布", generate_chart, filter_type="date_dropdown")
        # 初始載入
        available_dates = self.get_available_dates()
        initial_date = available_dates[0] if available_dates else datetime.now().strftime("%Y-%m-%d")
        generate_chart(window, "2000-01-01", initial_date, '全部')


class DailyReportApp:
    """每日報表應用程式"""

    def __init__(self, root):
        self.root = root
        self.data_file = "inventory_data.json"
        self.load_inventory_data()

    def load_inventory_data(self):
        """載入庫存數據並轉換為報表格式"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.products = data.get('products', {})
            self.transactions = data.get('transactions', [])

            # 轉換為DataFrame用於報表
            self.create_report_data()

        except Exception as e:
            messagebox.showerror("錯誤", f"載入數據失敗: {str(e)}")
            self.products = {}
            self.transactions = []
            self.report_data = pd.DataFrame()

    def create_report_data(self):
        """創建報表數據"""
        report_records = []

        # 基於交易記錄創建報表數據
        for transaction in self.transactions:
            if transaction['TransactionType'] != 'initial':  # 跳過初始化記錄
                record = {
                    '日期': pd.to_datetime(transaction['Timestamp']).date(),
                    '單別': 'A01' if transaction['TransactionType'] == 'in' else 'B01',
                    '單號': transaction.get('OrderID', transaction['TransactionType']),
                    '品號': transaction.get('ProductName', '')[:10],
                    '品名': transaction['ProductName'],
                    '數量': abs(transaction['Quantity']),
                    '價格': self.products.get(transaction['ProductName'], {}).get('cost', 100),
                    '金額': abs(transaction['Quantity']) * self.products.get(transaction['ProductName'], {}).get('cost',
                                                                                                                 100),
                    '進出別': '入庫' if transaction['TransactionType'] == 'in' else '出庫',
                    '客戶/供應商': '亮晶晶公司',
                    '送出碼': 'Y',
                    '備註': transaction.get('Notes', '')
                }
                report_records.append(record)

        self.report_data = pd.DataFrame(report_records)



