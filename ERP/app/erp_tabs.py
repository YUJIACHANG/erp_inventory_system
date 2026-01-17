import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import pandas as pd
from datetime import datetime
import os
import sys
import json
from tkcalendar import Calendar  # 需要安裝 tkcalendar 套件: pip install tkcalendar


# 確保可以導入自定義模組
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# 導入自定義模組
from inventory_core import Inventory
from inventory_core import ProductionManager
from inventory_core import Order


class ProductionManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("庫存日常異動")
        self.root.geometry("1200x700")  # 統一介面大小
        self.root.iconbitmap("assets/erp_icon.ico")
        
        # 初始化空的資料結構
        self.inventory = Inventory()
        self.inventory.products = {}  # 保持空白
        self.inventory.database_path = "working_data/inventory_data.json"  # 使用工作資料路徑
        self.production_manager = ProductionManager(self.inventory)
        
        # 資料來源追蹤
        self.current_data_source = {
            "inventory": None,
            "production": None, 
            "orders": None
        }
        
        # 確保工作資料目錄存在
        os.makedirs("working_data", exist_ok=True)
        os.makedirs("initial_data", exist_ok=True)
        
        # 創建主框架和頁面
        self.create_main_frame()
        self.create_notebook()
        self.create_order_page()
        self.create_production_page()
        self.create_inventory_page()
        
        # 檢查並自動載入工作資料
        self.auto_load_working_data()
        
        # 設定程式關閉時的處理
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def auto_load_working_data(self):
        """自動檢查並載入 working_data 資料夾中的 JSON 檔案"""
        print("檢查 working_data 資料夾...")
        
        # 檢查庫存資料
        inventory_file = "working_data/inventory_data.json"
        if os.path.exists(inventory_file):
            try:
                self.load_inventory_from_json(inventory_file)
                self.current_data_source["inventory"] = inventory_file
                self.inventory_source_label.config(text="目前資料來源: inventory_data.json (自動載入)")
                self.production_source_label.config(text="目前資料來源: inventory_data.json (自動載入)")
                print("✅ 已自動載入庫存資料")
            except Exception as e:
                print(f"❌ 自動載入庫存資料失敗: {e}")
        
        # 檢查訂單資料
        orders_file = "working_data/orders_data.json"
        if os.path.exists(orders_file):
            try:
                self.load_orders_from_json(orders_file)
                self.current_data_source["orders"] = orders_file
                self.order_source_label.config(text="目前資料來源: orders_data.json (自動載入)")
                print("✅ 已自動載入訂單資料")
            except Exception as e:
                print(f"❌ 自動載入訂單資料失敗: {e}")
        
        # 刷新所有顯示
        self.refresh_inventory()
        self.refresh_order_list()
        self.refresh_product_list()
        
        # 如果沒有載入任何資料，顯示空白介面
        if not any(self.current_data_source.values()):
            print("📋 沒有找到工作資料，顯示空白介面")
        
    def create_main_frame(self):
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
    def create_notebook(self):
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

    def create_order_page(self):
        self.order_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.order_frame, text="訂單管理")
        
        # 資料來源顯示區域
        source_frame = ttk.Frame(self.order_frame)
        source_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.order_source_label = ttk.Label(source_frame, text="目前資料來源: 無", font=("Arial", 9))
        self.order_source_label.pack(side=tk.LEFT)
        
        # 匯入訂單資料按鈕
        import_order_btn = ttk.Button(source_frame, text="匯入訂單資料", command=self.import_order_data)
        import_order_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # 上方篩選區域
        filter_frame = ttk.LabelFrame(self.order_frame, text="篩選條件", padding="10")
        filter_frame.pack(fill=tk.X, pady=5)

        # 使用網格布局，設置列權重以更好地分配空間
        filter_frame.columnconfigure(2, weight=1)
        filter_frame.columnconfigure(5, weight=1)
        
        # 日期篩選 - 不預設今天的日期
        ttk.Label(filter_frame, text="日期:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.date_var = tk.StringVar(value="")  # 改為空白，不預設今天
        date_entry = ttk.Entry(filter_frame, textvariable=self.date_var, width=9)
        date_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # 日曆按鈕
        def show_calendar():
            cal_window = tk.Toplevel(self.root)
            cal_window.title("選擇日期")
            cal_window.geometry("300x250")
            cal_window.transient(self.root)
            cal_window.grab_set()
            
            # 如果日期欄位有值，就用該日期初始化日曆，否則用今天
            current_date = datetime.now()
            if self.date_var.get() and '-' in self.date_var.get():
                try:
                    date_parts = self.date_var.get().split('-')
                    if len(date_parts) == 3:
                        current_date = datetime(int(date_parts[0]), int(date_parts[1]), int(date_parts[2]))
                except:
                    pass  # 如果解析失敗，就用今天的日期
            
            cal = Calendar(cal_window, selectmode="day", 
                        date_pattern="yyyy-mm-dd",
                        year=current_date.year,
                        month=current_date.month,
                        day=current_date.day)
            cal.pack(padx=10, pady=10, fill="both", expand=True)
            
            def set_date():
                selected_date = cal.selection_get()
                self.date_var.set(selected_date.strftime("%Y-%m-%d"))
                cal_window.destroy()
                self.refresh_order_list()
            
            button_frame = ttk.Frame(cal_window)
            button_frame.pack(padx=10, pady=10, fill="x")
            
            ttk.Button(button_frame, text="確認", command=set_date).pack(side="right", padx=5)
            ttk.Button(button_frame, text="取消", command=cal_window.destroy).pack(side="right", padx=5)
        
        cal_button = ttk.Button(filter_frame, text="選擇日期", command=show_calendar, width=7)
        cal_button.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        
        # 客戶篩選
        ttk.Label(filter_frame, text="客戶:").grid(row=0, column=3, padx=(60, 5), pady=5, sticky="e")
        self.customer_filter_var = tk.StringVar(value="全部")
        self.customer_combo = ttk.Combobox(filter_frame, textvariable=self.customer_filter_var, width=8)
        self.customer_combo['values'] = ["全部"]
        self.customer_combo.current(0)
        self.customer_combo.grid(row=0, column=4, padx=5, pady=5, sticky="w")
                
        # 狀態篩選
        ttk.Label(filter_frame, text="狀態:").grid(row=0, column=5, padx=(60, 5), pady=5, sticky="e")
        self.status_filter_var = tk.StringVar(value="全部")
        status_combo = ttk.Combobox(filter_frame, textvariable=self.status_filter_var, width=5)
        status_combo['values'] = ["全部", "新訂單",  "部分分配", "已分配", "已出貨", "已取消"]
        status_combo.current(0)
        status_combo.grid(row=0, column=6, padx=5, pady=5, sticky="w")
        
        # 篩選按鈕
        filter_btn = ttk.Button(filter_frame, text="篩選", command=self.refresh_order_list)
        filter_btn.grid(row=0, column=7, padx=(20, 5), pady=5)

        # 左側訂單列表
        order_list_frame = ttk.LabelFrame(self.order_frame, text="訂單列表", padding="10")
        order_list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 訂單列表
        columns = (
            "日期", "訂單編號", "客戶", "序號", "品號", "產品", "數量", 
            "單價", "金額", "尚可分配量", "現有庫存量", "狀態"
        )
        self.order_tree = ttk.Treeview(order_list_frame, columns=columns, show="headings")
        
        # 設定欄位標題和寬度
        column_widths = {
            "日期": 80, "訂單編號": 100, "客戶": 80, "序號": 50, 
            "品號": 70, "產品": 150, "數量": 50, "單價": 60, "金額": 70, 
            "尚可分配量": 80, "現有庫存量": 80, "狀態": 70
        }
        
        for col in columns:
            self.order_tree.heading(col, text=col)
            self.order_tree.column(col, width=column_widths.get(col, 100))
        
        # 添加滾動條
        order_scrollbar_y = ttk.Scrollbar(order_list_frame, orient="vertical", command=self.order_tree.yview)
        self.order_tree.configure(yscrollcommand=order_scrollbar_y.set)
        order_scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        order_scrollbar_x = ttk.Scrollbar(order_list_frame, orient="horizontal", command=self.order_tree.xview)
        self.order_tree.configure(xscrollcommand=order_scrollbar_x.set)
        order_scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.order_tree.pack(fill=tk.BOTH, expand=True)
        
        # 右側訂單操作
        order_action_frame = ttk.LabelFrame(self.order_frame, text="訂單操作", padding="10")
        order_action_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 新增訂單按鈕
        add_order_btn = ttk.Button(order_action_frame, text="新增訂單", command=self.add_order_dialog)
        add_order_btn.pack(fill=tk.X, pady=5)
        
        # 取消訂單按鈕
        cancel_order_btn = ttk.Button(order_action_frame, text="取消訂單", command=self.cancel_order)
        cancel_order_btn.pack(fill=tk.X, pady=5)
        
        # 分配庫存按鈕
        allocate_btn = ttk.Button(order_action_frame, text="分配庫存", command=self.allocate_inventory)
        allocate_btn.pack(fill=tk.X, pady=5)
        
        # 訂單出貨按鈕
        ship_btn = ttk.Button(order_action_frame, text="訂單出貨", command=self.ship_order_from_list)
        ship_btn.pack(fill=tk.X, pady=5)
        
        # 重新整理按鈕
        refresh_btn = ttk.Button(order_action_frame, text="重新整理", command=self.refresh_order_list)
        refresh_btn.pack(fill=tk.X, pady=5)
        
    def create_production_page(self):
        self.production_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.production_frame, text="生產管理")
        
        # 資料來源顯示區域
        source_frame = ttk.Frame(self.production_frame)
        source_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.production_source_label = ttk.Label(source_frame, text="目前資料來源: 無", font=("Arial", 9))
        self.production_source_label.pack(side=tk.LEFT)
        
        # 匯入生產資料按鈕
        import_prod_btn = ttk.Button(source_frame, text="匯入生產資料", command=self.import_production_data)
        import_prod_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # 左側品號列表
        product_list_frame = ttk.LabelFrame(self.production_frame, text="品號列表", padding="10")
        product_list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 品號列表
        columns = ("品號", "品名", "尚可分配量", "現有庫存量", "單位成本")
        self.product_tree = ttk.Treeview(product_list_frame, columns=columns, show="headings")
        
        column_widths = {"品號": 120, "品名": 200, "尚可分配量": 100, "現有庫存量": 100, "單位成本": 80}
        for col in columns:
            self.product_tree.heading(col, text=col)
            self.product_tree.column(col, width=column_widths.get(col, 100))
        
        product_scrollbar = ttk.Scrollbar(product_list_frame, orient="vertical", command=self.product_tree.yview)
        self.product_tree.configure(yscrollcommand=product_scrollbar.set)
        product_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.product_tree.pack(fill=tk.BOTH, expand=True)
        
        # 右側生產操作
        production_action_frame = ttk.LabelFrame(self.production_frame, text="生產操作", padding="10")
        production_action_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 生產數量框架
        prod_qty_frame = ttk.Frame(production_action_frame)
        prod_qty_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(prod_qty_frame, text="生產數量:").pack(side=tk.LEFT)
        self.prod_qty_var = tk.StringVar(value="10")
        prod_qty_entry = ttk.Entry(prod_qty_frame, textvariable=self.prod_qty_var, width=8)
        prod_qty_entry.pack(side=tk.RIGHT)
        
        # 生產按鈕
        produce_btn = ttk.Button(production_action_frame, text="生產", command=self.produce_from_product_list)
        produce_btn.pack(fill=tk.X, pady=5)
        
        # 重新整理按鈕
        refresh_prod_btn = ttk.Button(production_action_frame, text="重新整理", command=self.refresh_product_list)
        refresh_prod_btn.pack(fill=tk.X, pady=5)
        
    def create_inventory_page(self):
        self.inventory_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.inventory_frame, text="庫存管理")
        
        # 資料來源顯示區域
        source_frame = ttk.Frame(self.inventory_frame)
        source_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.inventory_source_label = ttk.Label(source_frame, text="目前資料來源: 無", font=("Arial", 9))
        self.inventory_source_label.pack(side=tk.LEFT)
        
        # 匯入庫存資料按鈕
        import_inv_btn = ttk.Button(source_frame, text="匯入庫存資料", command=self.import_inventory_data)
        import_inv_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # 左側品號列表
        inventory_list_frame = ttk.LabelFrame(self.inventory_frame, text="品號列表", padding="10")
        inventory_list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 品號列表
        columns = ("品號", "品名", "尚可分配量", "現有庫存量", "單位成本")
        self.inventory_tree = ttk.Treeview(inventory_list_frame, columns=columns, show="headings")
        
        column_widths = {"品號": 100, "品名": 200, "尚可分配量": 100, "現有庫存量": 100, "單位成本": 80}
        for col in columns:
            self.inventory_tree.heading(col, text=col)
            self.inventory_tree.column(col, width=column_widths.get(col, 100))
        
        inventory_scrollbar = ttk.Scrollbar(inventory_list_frame, orient="vertical", command=self.inventory_tree.yview)
        self.inventory_tree.configure(yscrollcommand=inventory_scrollbar.set)
        inventory_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.inventory_tree.pack(fill=tk.BOTH, expand=True)
        
        # 右側庫存操作
        inventory_action_frame = ttk.LabelFrame(self.inventory_frame, text="庫存操作", padding="10")
        inventory_action_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 新增庫存按鈕
        add_inv_btn = ttk.Button(inventory_action_frame, text="+ 新增庫存", command=self.add_inventory_dialog)
        add_inv_btn.pack(fill=tk.X, pady=5)
        
        # 調整數量框架
        adj_qty_frame = ttk.Frame(inventory_action_frame)
        adj_qty_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(adj_qty_frame, text="調整數量:").pack(side=tk.LEFT)
        self.adj_qty_var = tk.StringVar(value="0")
        adj_qty_entry = ttk.Entry(adj_qty_frame, textvariable=self.adj_qty_var, width=8)
        adj_qty_entry.pack(side=tk.RIGHT)
        
        # 調整按鈕
        adjust_btn = ttk.Button(inventory_action_frame, text="調整", command=self.adjust_inventory)
        adjust_btn.pack(fill=tk.X, pady=5)
        
        # 重新整理按鈕
        refresh_inv_btn = ttk.Button(inventory_action_frame, text="重新整理", command=self.refresh_inventory)
        refresh_inv_btn.pack(fill=tk.X, pady=5)

    def on_closing(self):
        """程式關閉時的處理"""
        try:
            self.auto_save_data()
            print("程式關閉前已自動儲存資料")
        except Exception as e:
            print(f"關閉時儲存失敗: {e}")
        finally:
            self.root.destroy()

    # ==================== 新增的匯入功能方法 ====================
    
    def import_order_data(self):
        """匯入訂單資料"""
        file_types = [
            ("All files", "*.*"),
            ("Excel files", "*.xlsx"), 
            ("JSON files", "*.json")
        ]
        
        file_path = filedialog.askopenfilename(
            title="選擇訂單資料檔案",
            filetypes=file_types,
            initialdir="initial_data"  # 從 initial_data 資料夾選擇
        )
        
        if file_path:
            try:
                if file_path.endswith('.json'):
                    self.load_orders_from_json(file_path)
                elif file_path.endswith('.xlsx'):
                    self.load_orders_from_excel(file_path)
                
                self.current_data_source["orders"] = file_path
                self.order_source_label.config(text=f"目前資料來源: {os.path.basename(file_path)}")
                
                # 刷新顯示
                self.refresh_order_list()
                
                # 自動儲存資料
                self.auto_save_data()
                
                messagebox.showinfo("成功", f"已成功匯入訂單資料：{os.path.basename(file_path)}")
                
            except Exception as e:
                messagebox.showerror("錯誤", f"匯入訂單資料失敗: {str(e)}")

    def import_production_data(self):
        """匯入生產資料"""
        file_types = [
            ("All files", "*.*"),
            ("Excel files", "*.xlsx"), 
            ("JSON files", "*.json")
        ]
        
        file_path = filedialog.askopenfilename(
            title="選擇生產資料檔案",
            filetypes=file_types,
            initialdir="initial_data"  # 從 initial_data 資料夾選擇
        )
        
        if file_path:
            try:
                if file_path.endswith('.json'):
                    self.load_production_from_json(file_path)
                elif file_path.endswith('.xlsx'):
                    self.load_production_from_excel(file_path)
                
                self.current_data_source["production"] = file_path
                self.production_source_label.config(text=f"目前資料來源: {os.path.basename(file_path)}")
                
                # 刷新顯示
                self.refresh_product_list()
                
                # 自動儲存資料
                self.auto_save_data()
                
                messagebox.showinfo("成功", f"已成功匯入生產資料：{os.path.basename(file_path)}")
                
            except Exception as e:
                messagebox.showerror("錯誤", f"匯入生產資料失敗: {str(e)}")

    def import_inventory_data(self):
        """匯入庫存資料"""
        file_types = [
            ("All files", "*.*"),
            ("Excel files", "*.xlsx"), 
            ("JSON files", "*.json")
        ]
        
        file_path = filedialog.askopenfilename(
            title="選擇庫存資料檔案",
            filetypes=file_types,
            initialdir="initial_data"  # 從 initial_data 資料夾選擇
        )
        
        if file_path:
            try:
                if file_path.endswith('.json'):
                    self.load_inventory_from_json(file_path)
                elif file_path.endswith('.xlsx'):
                    self.load_inventory_from_excel(file_path)
                
                self.current_data_source["inventory"] = file_path
                self.inventory_source_label.config(text=f"目前資料來源: {os.path.basename(file_path)}")
                
                # 刷新顯示
                self.refresh_inventory()
                self.refresh_product_list()  # 生產管理也需要更新
                
                # 自動儲存資料
                self.auto_save_data()
                
                messagebox.showinfo("成功", f"已成功匯入庫存資料：{os.path.basename(file_path)}")
                
            except Exception as e:
                messagebox.showerror("錯誤", f"匯入庫存資料失敗: {str(e)}")

    # ==================== 資料載入方法（修復版本）====================
    
    def load_orders_from_json(self, file_path):
        """從JSON檔案載入訂單資料"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 清空現有訂單
        self.production_manager.orders = {}
        
        orders_data = data.get('orders', [])
        order_keys_added = set()
        
        for order_data in orders_data:
            try:
                order = Order(
                    trans_type=order_data.get('trans_type', 'SO'),
                    trans_id=order_data.get('trans_id', ''),
                    seq_id=order_data.get('seq_id', '001'),
                    prod_id=order_data.get('prod_id', ''),
                    prod_name=order_data.get('prod_name', ''),
                    quantity=order_data.get('quantity', 0),
                    price=order_data.get('price', 0.0),
                    cust_id=order_data.get('cust_id', ''),
                    cust_name=order_data.get('cust_name', ''),
                    facto_id=order_data.get('facto_id', ''),
                    facto_name=order_data.get('facto_name', '')
                )
                
                # 設置額外屬性
                order.date = order_data.get('date', datetime.now().strftime("%Y-%m-%d"))
                order.status = order_data.get('status', '新訂單')
                order.allocated_quantity = order_data.get('allocated_quantity', 0)
                
                # 檢查重複
                order_key = order.order_key
                if order_key in order_keys_added:
                    print(f"警告：發現重複的訂單 {order_key}，跳過")
                    continue
                
                # 修復：使用 preserve_status=True 保留原有狀態
                self.production_manager.add_order(order, preserve_status=True)
                order_keys_added.add(order_key)
                
                print(f"已載入訂單 {order_key}，產品：{order.prod_name}，狀態：{order.status}")
                
            except Exception as e:
                print(f"處理訂單資料時發生錯誤: {e}")
                continue
        
        print(f"成功載入 {len(order_keys_added)} 筆訂單")

    def load_orders_from_excel(self, file_path):
        """從Excel檔案載入訂單資料"""
        df = pd.read_excel(file_path)
        
        # 清空現有訂單
        self.production_manager.orders = {}
        
        # 用於追蹤重複的訂單key
        order_keys_added = set()
        
        for index, row in df.iterrows():
            try:
                # 修復：正確讀取單價
                unit_price = float(row.get('單價', 0.0))
                
                # 構建訂單的唯一識別碼
                trans_id = str(row.get('單號', ""))
                seq_id = str(row.get('序號', "")).zfill(3)  # 確保序號是3位數格式
                order_key = f"{trans_id}-{seq_id}"
                
                # 檢查是否已經添加過這個訂單
                if order_key in order_keys_added:
                    print(f"警告：發現重複的訂單 {order_key}，跳過")
                    continue
                
                order = Order(
                    trans_type=row.get('交易類型', "SO"),
                    trans_id=trans_id,
                    seq_id=seq_id,
                    prod_id=row.get('品號', ""),
                    prod_name=row.get('品名', ""),
                    quantity=row.get('訂購數量', 0),
                    price=unit_price,
                    cust_id=row.get('客戶代號', ""),
                    cust_name=row.get('客戶名稱', ""),
                    facto_id=row.get('廠商代號', "F001"),
                    facto_name=row.get('廠商名稱', "預設廠商")
                )
                
                # 設置訂單的日期和狀態 - 保留原始狀態
                order.date = str(row.get('提交日期', ""))
                order.status = str(row.get('狀態', "新訂單"))
                order.allocated_quantity = row.get('已分配量', 0)  # 新增：讀取已分配量
                
                # 修復：使用 preserve_status=True 保留原有狀態
                self.production_manager.add_order(order, preserve_status=True)
                order_keys_added.add(order_key)
                
                print(f"已載入訂單 {order_key}，產品：{order.prod_name}，狀態：{order.status}")
                
                # 確保對應的產品存在於庫存中
                product_name = order.prod_name
                if product_name not in self.inventory.products:
                    initial_quantity = int(row.get('現有庫存量', 0))
                    self.inventory.add_product(product_name, initial_quantity=initial_quantity)
                    self.inventory.products[product_name]['cost'] = 100.0
                    self.inventory.products[product_name]['allocatable'] = int(row.get('尚可分配量', 0))
                    self.inventory.products[product_name]['product_id'] = row.get('品號', "")
            
            except Exception as e:
                print(f"處理第 {index+1} 行訂單資料時發生錯誤: {e}")
                print(f"該行資料: {dict(row)}")
                continue
        
        print(f"成功載入 {len(order_keys_added)} 筆訂單")

    def load_production_from_json(self, file_path):
        """從JSON檔案載入生產資料"""
        # 生產資料主要是庫存資料的子集，所以調用庫存載入
        self.load_inventory_from_json(file_path)

    def load_production_from_excel(self, file_path):
        """從Excel檔案載入生產資料"""
        # 生產資料主要是庫存資料的子集，所以調用庫存載入
        self.load_inventory_from_excel(file_path)

    def load_inventory_from_json(self, file_path):
        """從JSON檔案載入庫存資料"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 清空現有庫存
        self.inventory.products = {}
        
        products_data = data.get('products', {})
        for product_name, product_info in products_data.items():
            self.inventory.products[product_name] = product_info

    def load_inventory_from_excel(self, file_path):
        """從Excel檔案載入庫存資料"""
        df = pd.read_excel(file_path)
        
        # 清空現有庫存
        self.inventory.products = {}
        
        for _, row in df.iterrows():
            try:
                product_name = str(row['品名'])
                product_id = str(row['品號'])
                unit_cost = float(row['單位成本'])
                allocatable_qty = int(row['尚可分配量'])
                current_stock = int(row['現有庫存量'])
                
                # 新增產品到庫存系統
                if product_name not in self.inventory.products:
                    self.inventory.add_product(product_name, initial_quantity=current_stock)
                    
                    # 設置產品的詳細資訊
                    self.inventory.products[product_name]['cost'] = unit_cost
                    self.inventory.products[product_name]['allocatable'] = allocatable_qty
                    self.inventory.products[product_name]['product_id'] = product_id
                    
            except Exception as e:
                print(f"處理庫存資料時發生錯誤: {e}")
                continue

    # ==================== 自動儲存功能 ====================
    
    def auto_save_data(self):
        """自動儲存所有資料到JSON檔案"""
        try:
            # 儲存庫存資料
            if self.inventory.products:
                inventory_data = {
                    'products': self.inventory.products,
                    'transactions': [t.to_dict() for t in self.inventory.transactions] if hasattr(self.inventory, 'transactions') else []
                }
                with open("working_data/inventory_data.json", 'w', encoding='utf-8') as f:
                    json.dump(inventory_data, f, ensure_ascii=False, indent=4)
                print("✅ 庫存資料已儲存")
            
            # 儲存訂單資料 - 即使是空的也要儲存
            orders_data = []
            if self.production_manager.orders:
                for order_key, order in self.production_manager.orders.items():
                    order_dict = {
                        'trans_type': order.trans_type,
                        'trans_id': order.trans_id,
                        'seq_id': order.seq_id,
                        'prod_id': order.prod_id,
                        'prod_name': order.prod_name,
                        'quantity': order.quantity,
                        'price': order.price,
                        'cust_id': order.cust_id,
                        'cust_name': order.cust_name,
                        'facto_id': order.facto_id,
                        'facto_name': order.facto_name,
                        'date': getattr(order, 'date', datetime.now().strftime("%Y-%m-%d")),
                        'status': order.status,
                        'allocated_quantity': getattr(order, 'allocated_quantity', 0)
                    }
                    orders_data.append(order_dict)
            
            # 總是儲存訂單檔案，即使是空的
            order_save_data = {'orders': orders_data}
            with open("working_data/orders_data.json", 'w', encoding='utf-8') as f:
                json.dump(order_save_data, f, ensure_ascii=False, indent=4)
            
            print(f"✅ 訂單資料已儲存 ({len(orders_data)} 筆訂單)")
            print("✅ 資料已自動儲存至 working_data/ 目錄")
            
        except Exception as e:
            print(f"❌ 自動儲存失敗: {str(e)}")
            # 顯示錯誤訊息給使用者
            messagebox.showwarning("儲存警告", f"資料儲存時發生問題: {str(e)}")

    # ==================== 原有的功能方法（保持不變）====================
    
    def add_inventory_dialog(self):
        """新增庫存對話框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("新增庫存")
        dialog.geometry("300x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="品號:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        product_id_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=product_id_var).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(dialog, text="品名:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        product_name_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=product_name_var).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(dialog, text="初始庫存:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        quantity_var = tk.StringVar(value="0")
        ttk.Entry(dialog, textvariable=quantity_var).grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(dialog, text="單位成本:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        cost_var = tk.StringVar(value="0.0")
        ttk.Entry(dialog, textvariable=cost_var).grid(row=3, column=1, padx=5, pady=5)
        
        def confirm_add_inventory():
            try:
                product_id = product_id_var.get().strip()
                product_name = product_name_var.get().strip()
                quantity = int(quantity_var.get())
                cost = float(cost_var.get())
                
                if not product_name:
                    messagebox.showerror("錯誤", "請填寫品名")
                    return
                
                if product_name in self.inventory.products:
                    messagebox.showerror("錯誤", f"產品 '{product_name}' 已存在")
                    return
                
                # 新增產品
                self.inventory.add_product(product_name, initial_quantity=quantity)
                self.inventory.products[product_name]['cost'] = cost
                self.inventory.products[product_name]['allocatable'] = quantity
                self.inventory.products[product_name]['product_id'] = product_id or f"P{hash(product_name) % 1000:03d}"
                
                dialog.destroy()
                self.refresh_inventory()
                self.refresh_product_list()
                self.auto_save_data()
                messagebox.showinfo("成功", f"已新增產品 '{product_name}'")
                
            except ValueError:
                messagebox.showerror("錯誤", "數量和成本必須是數字")
            except Exception as e:
                messagebox.showerror("錯誤", f"新增產品失敗: {str(e)}")
        
        ttk.Button(dialog, text="確認", command=confirm_add_inventory).grid(row=4, column=0, columnspan=2, pady=10)
    
    def adjust_inventory(self):
        """調整庫存數量"""
        if not self.inventory_tree.selection():
            messagebox.showinfo("提示", "請先選擇一個產品")
            return
        
        item = self.inventory_tree.selection()[0]
        product_name = self.inventory_tree.item(item, "values")[1]  # 品名在第二列
        
        try:
            adjust_qty = int(self.adj_qty_var.get())
            
            if product_name not in self.inventory.products:
                messagebox.showerror("錯誤", f"找不到產品 '{product_name}'")
                return
            
            current_qty = self.inventory.products[product_name]["quantity"]
            new_qty = current_qty + adjust_qty
            
            if new_qty < 0:
                messagebox.showerror("錯誤", f"調整後庫存數量不能小於0，當前: {current_qty}, 調整: {adjust_qty}")
                return
            
            # 調整庫存
            if adjust_qty > 0:
                self.inventory.stock_in(product_name, adjust_qty, "手動調整")
                # 增加尚可分配量
                self.inventory.products[product_name]['allocatable'] += adjust_qty
            elif adjust_qty < 0:
                self.inventory.stock_out(product_name, abs(adjust_qty), "手動調整", "手動調整")
                # 減少尚可分配量，但不能小於0
                allocatable = self.inventory.products[product_name].get('allocatable', 0)
                self.inventory.products[product_name]['allocatable'] = max(0, allocatable + adjust_qty)
            
            self.adj_qty_var.set("0")  # 重置調整數量
            self.refresh_inventory()
            self.refresh_product_list()
            self.refresh_order_list()
            self.auto_save_data()  # 自動儲存
            messagebox.showinfo("成功", f"已調整產品 '{product_name}' 的庫存，調整量: {adjust_qty}")
            
        except ValueError:
            messagebox.showerror("錯誤", "調整數量必須是整數")
    
    def refresh_inventory(self):
        """刷新庫存列表"""
        # 清空現有列表
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)
        
        # 獲取所有庫存
        inventory = self.inventory.check_stocks()
        
        # 添加到列表 - 包含成本資訊
        for product, info in inventory.items():
            allocatable = info.get('allocatable', 0)
            cost = info.get('cost', 0.0)
            product_id = info.get('product_id', "P" + str(hash(product) % 1000))  # 使用實際品號或生成簡單品號
            
            self.inventory_tree.insert("", tk.END, values=(
                product_id,
                product,
                allocatable,
                info["quantity"],
                f"{cost:.2f}"  # 格式化成本為兩位小數
            ))
    
    def refresh_product_list(self):
        """刷新品號列表"""
        # 清空現有列表
        for item in self.product_tree.get_children():
            self.product_tree.delete(item)
        
        # 獲取所有庫存
        inventory = self.inventory.check_stocks()
        
        # 添加到列表 - 包含成本資訊
        for product, info in inventory.items():
            allocatable = info.get('allocatable', 0)
            cost = info.get('cost', 0.0)
            product_id = info.get('product_id', "P" + str(hash(product) % 1000))  # 使用實際品號或生成簡單品號
            
            self.product_tree.insert("", tk.END, values=(
                product_id,
                product,
                allocatable,
                info["quantity"],
                f"{cost:.2f}"  # 格式化成本為兩位小數
            ))
    
    def produce_from_product_list(self):
        """從品號列表生產產品"""
        if not self.product_tree.selection():
            messagebox.showinfo("提示", "請先選擇一個產品")
            return
        
        item = self.product_tree.selection()[0]
        product_name = self.product_tree.item(item, "values")[1]  # 品名在第二列
        
        try:
            quantity = int(self.prod_qty_var.get())
            if quantity <= 0:
                messagebox.showerror("錯誤", "生產數量必須大於0")
                return
            
            # 增加庫存
            self.inventory.stock_in(product_name, quantity, "生產")
            
            # 增加尚可分配量
            self.inventory.products[product_name]['allocatable'] += quantity
            
            self.refresh_product_list()
            self.refresh_inventory()
            self.refresh_order_list()
            self.auto_save_data()  # 自動儲存
            messagebox.showinfo("成功", f"已生產 {quantity} 個 {product_name}")
            
        except ValueError:
            messagebox.showerror("錯誤", "生產數量必須是整數")
    
    def add_order_dialog(self):
        """新增訂單對話框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("新增訂單")
        dialog.geometry("800x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 單頭框架
        header_frame = ttk.LabelFrame(dialog, text="訂單資訊", padding="10")
        header_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 日期
        ttk.Label(header_frame, text="日期:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        order_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        date_entry = ttk.Entry(header_frame, textvariable=order_date_var, width=12)
        date_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # 日曆按鈕
        def select_date():
            def set_date():
                selected_date = cal.selection_get()
                order_date_var.set(selected_date.strftime("%Y-%m-%d"))
                date_top.destroy()
            
            date_top = tk.Toplevel(dialog)
            date_top.title("選擇日期")
            date_top.geometry("300x250")
            date_top.transient(dialog)
            date_top.grab_set()
            
            cal = Calendar(date_top, selectmode="day", date_pattern="yyyy-mm-dd")
            cal.pack(padx=10, pady=10)
            
            ttk.Button(date_top, text="確定", command=set_date).pack(pady=5)
        
        cal_btn = ttk.Button(header_frame, text="選擇日期", command=select_date, width=8)
        cal_btn.grid(row=0, column=2, padx=5, pady=5)
        
        # 訂單編號 - 修改格式為 SO2 + 日期 + 序號
        ttk.Label(header_frame, text="訂單編號:").grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        order_id_var = tk.StringVar(value=f"SO2{datetime.now().strftime('%Y%m%d')}-001")
        ttk.Entry(header_frame, textvariable=order_id_var, width=15).grid(row=0, column=4, padx=5, pady=5)
        
        # 客戶代號 - 使用和篩選條件一樣的客戶列表
        ttk.Label(header_frame, text="客戶代號:").grid(row=0, column=5, sticky=tk.W, padx=5, pady=5)
        customer_var = tk.StringVar()
        customer_combo = ttk.Combobox(header_frame, textvariable=customer_var, width=15)
        
        # 獲取現有訂單中的所有客戶名稱（和篩選條件使用相同的邏輯）
        all_order_objects = list(self.production_manager.orders.values())
        all_customers = set()
        for order_obj in all_order_objects:
            if order_obj.cust_name:
                all_customers.add(order_obj.cust_name)
        
        # 設置客戶下拉選單選項（不包含"全部"，因為新增訂單必須選擇具體客戶）
        customer_list = sorted(list(all_customers))
        if not customer_list:
            # 如果沒有現有客戶，提供一些預設選項
            customer_list = ["客戶A", "客戶B", "客戶C"]
        
        customer_combo['values'] = customer_list
        customer_combo.grid(row=0, column=6, padx=5, pady=5)
        
        # 單身框架
        detail_frame = ttk.LabelFrame(dialog, text="訂單明細", padding="10")
        detail_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 明細表格標題
        columns = ("序號", "產品", "數量", "單價", "金額")
        detail_tree = ttk.Treeview(detail_frame, columns=columns, show="headings", height=10)
        
        # 設定欄位標題和寬度
        column_widths = {"序號": 50, "產品": 250, "數量": 80, "單價": 100, "金額": 100}
        for col in columns:
            detail_tree.heading(col, text=col)
            detail_tree.column(col, width=column_widths.get(col, 100))
        
        # 添加滾動條
        detail_scrollbar = ttk.Scrollbar(detail_frame, orient="vertical", command=detail_tree.yview)
        detail_tree.configure(yscrollcommand=detail_scrollbar.set)
        detail_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        detail_tree.pack(fill=tk.BOTH, expand=True)
        
        # 預先添加10行
        for i in range(1, 11):
            detail_tree.insert("", tk.END, values=(f"{i:02d}", "", "", "", ""))
        
        # 編輯區域
        edit_frame = ttk.Frame(dialog, padding="10")
        edit_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 序號顯示（不可編輯）
        ttk.Label(edit_frame, text="序號:").grid(row=0, column=0, padx=5, pady=5)
        seq_var = tk.StringVar(value="1")  # 預設值為1
        seq_label = ttk.Label(edit_frame, textvariable=seq_var, width=5, relief="sunken", anchor="center")
        seq_label.grid(row=0, column=1, padx=5, pady=5)
        
        # 產品選擇
        ttk.Label(edit_frame, text="產品:").grid(row=0, column=2, padx=5, pady=5)
        product_var = tk.StringVar()
        product_combo = ttk.Combobox(edit_frame, textvariable=product_var, width=30)
        product_combo['values'] = list(self.inventory.products.keys())
        product_combo.grid(row=0, column=3, padx=5, pady=5)
        
        # 數量輸入
        ttk.Label(edit_frame, text="數量:").grid(row=0, column=4, padx=5, pady=5)
        quantity_var = tk.StringVar()
        quantity_entry = ttk.Entry(edit_frame, textvariable=quantity_var, width=8)
        quantity_entry.grid(row=0, column=5, padx=5, pady=5)
        
        # 單價輸入
        ttk.Label(edit_frame, text="單價:").grid(row=0, column=6, padx=5, pady=5)
        price_var = tk.StringVar()
        price_entry = ttk.Entry(edit_frame, textvariable=price_var, width=10)
        price_entry.grid(row=0, column=7, padx=5, pady=5)

        # 更新明細行
        def update_line():
            try:
                seq = int(seq_var.get())  # 從標籤取得當前序號
                
                if seq < 1 or seq > 10:
                    messagebox.showerror("錯誤", "序號超出範圍(1-10)")
                    return
                    
                product = product_var.get()
                quantity_str = quantity_var.get()
                price_str = price_var.get()
                
                # 驗證輸入
                if not product:
                    messagebox.showerror("錯誤", "請選擇產品")
                    product_combo.focus()
                    return
                    
                if not quantity_str:
                    messagebox.showerror("錯誤", "請輸入數量")
                    quantity_entry.focus()
                    return
                    
                if not price_str:
                    messagebox.showerror("錯誤", "請輸入單價")
                    price_entry.focus()
                    return
                
                try:
                    quantity = int(quantity_str)
                    price = float(price_str)
                except ValueError:
                    messagebox.showerror("錯誤", "數量必須是整數，單價必須是數字")
                    return
                    
                if quantity <= 0:
                    messagebox.showerror("錯誤", "數量必須大於0")
                    quantity_entry.focus()
                    return
                    
                if price <= 0:
                    messagebox.showerror("錯誤", "單價必須大於0")
                    price_entry.focus()
                    return
                
                amount = int(quantity * price)  # 取整數
                
                # 更新表格中對應的行
                item_id = detail_tree.get_children()[seq-1]
                detail_tree.item(item_id, values=(f"{seq:02d}", product, quantity, f"{price:.2f}", amount))
                
                # 清空輸入欄位
                product_var.set("")
                quantity_var.set("")
                price_var.set("")
                
                # 自動遞增序號（如果還在範圍內）
                if seq < 10:
                    seq_var.set(str(seq + 1))
                    product_combo.focus()
                else:
                    messagebox.showinfo("提示", "已達到最大明細行數(10行)")
                    
            except Exception as e:
                messagebox.showerror("錯誤", f"更新明細時發生錯誤: {str(e)}")

        update_btn = ttk.Button(edit_frame, text="更新明細", command=update_line)
        update_btn.grid(row=0, column=8, padx=10, pady=5)

        # 按鈕區域
        button_frame = ttk.Frame(dialog, padding="10")
        button_frame.pack(fill=tk.X, padx=10, pady=5)

        def confirm():
            try:
                # 檢查客戶是否填寫
                if not customer_var.get():
                    messagebox.showerror("錯誤", "請選擇客戶")
                    return
                
                # 檢查是否有至少一行明細
                has_detail = False
                order_details = []
                
                for item_id in detail_tree.get_children():
                    values = detail_tree.item(item_id, "values")
                    if values[1]:  # 如果產品欄位有填寫
                        has_detail = True
                        order_details.append({
                            "seq_id": values[0],
                            "product": values[1],
                            "quantity": int(values[2]),
                            "price": float(values[3]),
                            "amount": int(values[4])
                        })
                
                if not has_detail:
                    messagebox.showerror("錯誤", "請至少填寫一行明細")
                    return
                
                # 創建訂單
                order_date = order_date_var.get()
                order_id = order_id_var.get()  # 基礎訂單編號
                customer = customer_var.get()
                
                # 修正：為每個訂單明細創建獨立的訂單，使用不同的訂單ID
                for detail in order_details:
                    # 為每個明細創建唯一的訂單ID（基礎ID + 序號）
                    unique_order_id = f"{order_id}-{detail['seq_id']}"
                    
                    order = Order(
                        trans_type="SO2",  # 使用 SO2 作為交易類型
                        trans_id=unique_order_id,  # 使用唯一的訂單ID
                        seq_id=detail["seq_id"],
                        prod_id="P" + str(hash(detail["product"]) % 1000),
                        prod_name=detail["product"],
                        quantity=detail["quantity"],
                        price=detail["price"],
                        cust_id="C" + str(hash(customer) % 1000),
                        cust_name=customer,
                        facto_id="F001",
                        facto_name="預設廠商"
                    )
                    
                    # 設置訂單的日期
                    order.date = order_date
                    
                    # 設置訂單的已分配量為0
                    order.allocated_quantity = 0
                    
                    # 修復：使用 preserve_status=False，新增的訂單應該是「新訂單」
                    self.production_manager.add_order(order, preserve_status=False)
                
                dialog.destroy()
                self.refresh_order_list()
                self.refresh_product_list()
                self.auto_save_data()  # 自動儲存
                messagebox.showinfo("成功", f"已新增訂單 {order_id}，共 {len(order_details)} 項明細")
                
            except Exception as e:
                messagebox.showerror("錯誤", f"新增訂單失敗: {str(e)}")

        ttk.Button(button_frame, text="確認", command=confirm).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        
        # 設置初始焦點到產品選擇框
        product_combo.focus()

    def get_order_key_from_ui(self, item):
        """從UI選中的項目獲取完整的訂單key（修復版本）"""
        values = self.order_tree.item(item, "values")
        order_id = values[1]  # 訂單編號
        seq_id = values[3]    # 序號
        
        # 修復：確保序號格式一致（3位數）
        seq_id_formatted = str(seq_id).zfill(3)
        
        # 構建完整的訂單key: 訂單編號-序號
        order_key = f"{order_id}-{seq_id_formatted}"
        
        print(f"從UI獲取訂單key: {order_key}")
        return order_key

    def cancel_order(self):
        """取消訂單"""
        if not self.order_tree.selection():
            messagebox.showinfo("提示", "請先選擇一個訂單")
            return
                
        item = self.order_tree.selection()[0]
        order_key = self.get_order_key_from_ui(item)
            
        if messagebox.askyesno("確認", f"確定要取消訂單 {order_key} 嗎?"):
            # 獲取訂單資訊
            order_info = self.production_manager.get_order_status(order_key)
            if not order_info:
                messagebox.showerror("錯誤", f"無法獲取訂單 {order_key} 的資訊")
                return
                
            # 如果訂單已經分配了庫存，需要返回庫存
            product_name = order_info["產品"]
            allocated_quantity = order_info.get("已分配量", 0)
                
            if allocated_quantity > 0 and product_name in self.inventory.products:
                # 返回庫存的尚可分配量
                self.inventory.products[product_name]['allocatable'] += allocated_quantity
                
            # 取消訂單
            result = self.production_manager.cancel_order(order_key)
            if result:
                messagebox.showinfo("成功", f"訂單 {order_key} 已取消")
                self.refresh_order_list()
                self.refresh_product_list()
                self.refresh_inventory()
                self.auto_save_data()  # 自動儲存
            else:
                messagebox.showerror("錯誤", f"無法取消訂單 {order_key}")

    def allocate_inventory(self):
        """分配庫存到訂單"""
        if not self.order_tree.selection():
            messagebox.showinfo("提示", "請先選擇一個訂單")
            return
                
        item = self.order_tree.selection()[0]
        order_key = self.get_order_key_from_ui(item)
            
        # 獲取訂單資訊
        order_info = self.production_manager.get_order_status(order_key)
        if not order_info:
            messagebox.showerror("錯誤", f"無法獲取訂單 {order_key} 的資訊")
            return
            
        # 檢查訂單狀態
        if order_info["狀態"] != "新訂單":
            messagebox.showerror("錯誤", f"只有新訂單可以分配庫存，當前狀態: {order_info['狀態']}")
            return
            
        product_name = order_info["產品"]
        required_quantity = order_info["數量"]
        allocated_quantity = order_info.get("已分配量", 0)
        remaining_quantity = required_quantity - allocated_quantity
            
        if remaining_quantity <= 0:
            messagebox.showinfo("提示", "此訂單已完全分配")
            return
            
        # 檢查庫存是否足夠
        if product_name not in self.inventory.products:
            messagebox.showerror("錯誤", f"產品 '{product_name}' 不存在於庫存中")
            return
            
        allocatable_quantity = self.inventory.products[product_name].get('allocatable', 0)
            
        if allocatable_quantity <= 0:
            messagebox.showerror("錯誤", "沒有可分配的庫存")
            return
            
        # 計算可分配的數量
        quantity_to_allocate = min(allocatable_quantity, remaining_quantity)
            
        if quantity_to_allocate <= 0:
            messagebox.showerror("錯誤", "沒有可分配的庫存")
            return
            
        # 確認分配
        if messagebox.askyesno("確認", f"確定要分配 {quantity_to_allocate} 個 {product_name} 到訂單 {order_key} 嗎?"):
            # 減少尚可分配量
            self.inventory.products[product_name]['allocatable'] -= quantity_to_allocate
                
            # 更新訂單的已分配量
            order = self.production_manager.orders.get(order_key)
            if order:
                order.allocated_quantity = allocated_quantity + quantity_to_allocate
                    
                # 如果全部分配完成，更新狀態
                if order.allocated_quantity >= order.quantity:
                    order.status = "已分配"
                else:
                    order.status = "部分分配"
                    
                messagebox.showinfo("成功", f"已分配 {quantity_to_allocate} 個 {product_name} 到訂單 {order_key}")
                self.refresh_order_list()
                self.refresh_product_list()
                self.refresh_inventory()
                self.auto_save_data()  # 自動儲存
            else:
                messagebox.showerror("錯誤", f"找不到訂單 {order_key}")

    def ship_order_from_list(self):
        """從訂單列表出貨訂單"""
        if not self.order_tree.selection():
            messagebox.showinfo("提示", "請先選擇一個訂單")
            return
        
        item = self.order_tree.selection()[0]
        order_key = self.get_order_key_from_ui(item)
        
        # 檢查訂單狀態
        order_info = self.production_manager.get_order_status(order_key)
        if not order_info:
            messagebox.showerror("錯誤", f"無法獲取訂單 {order_key} 的資訊")
            return
        
        if order_info["狀態"] != "已分配" and order_info["狀態"] != "部分分配":
            messagebox.showerror("錯誤", f"只有已分配的訂單才能出貨，當前狀態: {order_info['狀態']}")
            return
        
        # 檢查庫存是否足夠
        product_name = order_info["產品"]
        allocated_quantity = order_info.get("已分配量", 0)
        
        if allocated_quantity <= 0:
            messagebox.showerror("錯誤", "此訂單沒有分配庫存，無法出貨")
            return
        
        if product_name not in self.inventory.products:
            messagebox.showerror("錯誤", f"產品 '{product_name}' 不存在於庫存中")
            return
        
        available_stock = self.inventory.products[product_name]["quantity"]
        
        if available_stock < allocated_quantity:
            messagebox.showerror("錯誤", f"庫存不足！需要: {allocated_quantity}, 可用: {available_stock}")
            return
        
        # 確認出貨
        if messagebox.askyesno("確認", f"確定要出貨訂單 {order_key} 嗎? 將從庫存扣除 {allocated_quantity} 個 {product_name}"):
            # 從庫存中扣除
            result = self.inventory.stock_out(
                product_name, 
                allocated_quantity, 
                order_key, 
                f"出貨訂單 {order_key}"
            )
            
            if result:
                # 更新訂單狀態
                order = self.production_manager.orders.get(order_key)
                if order:
                    order.status = "已出貨"
                    
                    messagebox.showinfo("成功", f"訂單 {order_key} 已出貨")
                    self.refresh_order_list()
                    self.refresh_product_list()
                    self.refresh_inventory()
                    self.auto_save_data()  # 自動儲存
                else:
                    messagebox.showerror("錯誤", f"找不到訂單 {order_key}")
            else:
                messagebox.showerror("錯誤", f"從庫存扣除失敗")

    def refresh_order_list(self):
        """刷新訂單列表（修復版本）"""
        # 清空現有列表
        for item in self.order_tree.get_children():
            self.order_tree.delete(item)
        
        # 獲取所有訂單物件（不是基本資訊）
        all_order_objects = list(self.production_manager.orders.values())
        
        print(f"總共有 {len(all_order_objects)} 筆訂單")
        
        # 收集所有客戶名稱
        all_customers = set()
        for order_obj in all_order_objects:
            if order_obj.cust_name:
                all_customers.add(order_obj.cust_name)
        
        # 更新客戶下拉選單選項
        customer_list = ["全部"] + sorted(list(all_customers))
        current_selection = self.customer_filter_var.get()
        self.customer_combo['values'] = customer_list
        
        # 如果當前選擇的客戶不在新的列表中，則重設為「全部」
        if current_selection not in customer_list:
            self.customer_filter_var.set("全部")
            self.customer_combo.current(0)
        
        # 應用篩選條件
        filtered_orders = []
        for order_obj in all_order_objects:
            # 篩選日期 - 修改邏輯，如果日期欄位為空則不篩選日期
            order_date = getattr(order_obj, 'date', '')
            if self.date_var.get() and self.date_var.get() != order_date:
                continue
            
            # 篩選客戶
            if self.customer_filter_var.get() != "全部" and self.customer_filter_var.get() != order_obj.cust_name:
                continue
            
            # 篩選狀態
            if self.status_filter_var.get() != "全部" and self.status_filter_var.get() != order_obj.status:
                continue
            
            filtered_orders.append(order_obj)
        
        print(f"篩選後有 {len(filtered_orders)} 筆訂單")
        
        # 添加到列表 - 修改欄位順序，將品號放在產品前面
        for order in filtered_orders:
            # 獲取產品庫存
            product_name = order.prod_name
            stock_quantity = 0
            allocatable_quantity = 0
            product_id = ""  # 初始化品號
            
            if product_name in self.inventory.products:
                stock_quantity = self.inventory.products[product_name]["quantity"]
                allocatable_quantity = self.inventory.products[product_name].get('allocatable', 0)
                product_id = self.inventory.products[product_name].get('product_id', order.prod_id)  # 獲取實際品號
            else:
                product_id = order.prod_id  # 如果庫存中沒有，使用訂單中的品號
            
            # 修復：直接從訂單物件獲取單價
            price = getattr(order, 'price', 0.0)
            quantity = order.quantity
            amount = int(price * quantity)

            # 處理訂單編號顯示格式：移除後面的序號部分（如 -01, -02 等）
            display_order_id = order.trans_id
            
            # 取得已分配量
            allocated_quantity = getattr(order, 'allocated_quantity', 0)
            
            values = (
                getattr(order, 'date', datetime.now().strftime("%Y-%m-%d")),
                display_order_id,  # 顯示用的訂單編號
                order.cust_name,
                getattr(order, 'seq_id', "001"),
                product_id,  # 品號
                product_name,  # 產品
                quantity,
                f"{price:.2f}",
                amount,
                allocatable_quantity,
                stock_quantity,
                order.status  # 保持原始狀態
            )
            self.order_tree.insert("", tk.END, values=values)
            
            print(f"顯示訂單：{order.order_key}，狀態：{order.status}")


# 主程式
def main():
    root = tk.Tk()
    app = ProductionManagerGUI(root)
    
    # 設置應用程式圖示
    try:
        root.iconbitmap("assets/erp_icon.ico")  # 如果有圖示檔案的話
    except:
        pass
        
    # 設置視窗大小和位置
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    width = 1200
    height = 700
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    root.geometry(f"{width}x{height}+{x}+{y}")
        
    root.mainloop()

if __name__ == "__main__":
    main()