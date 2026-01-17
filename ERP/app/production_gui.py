import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import pandas as pd
from datetime import datetime
from production_manager import ProductionManager 

# 假設Order類已經存在，這裡簡單模擬一下
class Order:
    def __init__(self, TransID, ProdName, Quantity, CustName):
        self.TransID = TransID
        self.ProdName = ProdName
        self.Quantity = Quantity
        self.CustName = CustName
        self.status = "新訂單"
        self.produced_quantity = 0
        self.order_date = datetime.now()

class ProductionManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("庫存管理系統")
        self.root.geometry("1000x600")
        try:
            self.root.iconbitmap(os.path.join("assets", "erp_icon.ico"))
        except Exception as e:
            print(f"載入圖示失敗: {e}")
                
        # 初始化生產管理器
        # from inventory import Inventory  # 假設inventory.py存在
        self.production_manager = ProductionManager()
        
        # 創建主框架
        self.create_main_frame()
        
        # 創建標籤頁
        self.create_notebook()
        
        # 創建訂單管理頁面
        self.create_order_page()
        
        # 創建生產管理頁面
        self.create_production_page()
        
        # 創建庫存管理頁面
        self.create_inventory_page()
        
    def create_main_frame(self):
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
    def create_notebook(self):
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
    def create_order_page(self):
        self.order_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.order_frame, text="訂單管理")
        
        # 左側訂單列表
        order_list_frame = ttk.LabelFrame(self.order_frame, text="訂單列表", padding="10")
        order_list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 訂單列表
        columns = ("訂單編號", "產品", "數量", "客戶", "狀態")
        self.order_tree = ttk.Treeview(order_list_frame, columns=columns, show="headings")
        
        # 設定欄位標題
        for col in columns:
            self.order_tree.heading(col, text=col)
            self.order_tree.column(col, width=100)
        
        self.order_tree.pack(fill=tk.BOTH, expand=True)
        self.order_tree.bind("<Double-1>", self.show_order_details)
        
        # 右側訂單操作
        order_action_frame = ttk.LabelFrame(self.order_frame, text="訂單操作", padding="10")
        order_action_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 新增訂單按鈕
        add_order_btn = ttk.Button(order_action_frame, text="新增訂單", command=self.add_order_dialog)
        add_order_btn.pack(fill=tk.X, pady=5)
        
        # 取消訂單按鈕
        cancel_order_btn = ttk.Button(order_action_frame, text="取消訂單", command=self.cancel_order)
        cancel_order_btn.pack(fill=tk.X, pady=5)
        
        # 重新整理按鈕
        refresh_btn = ttk.Button(order_action_frame, text="重新整理", command=self.refresh_order_list)
        refresh_btn.pack(fill=tk.X, pady=5)
        
    def create_production_page(self):
        self.production_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.production_frame, text="生產管理")
        
        # 左側待生產訂單
        pending_frame = ttk.LabelFrame(self.production_frame, text="待生產訂單", padding="10")
        pending_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 待生產訂單列表
        columns = ("訂單編號", "產品", "數量", "狀態", "已生產", "剩餘")
        self.production_tree = ttk.Treeview(pending_frame, columns=columns, show="headings")
        
        # 設定欄位標題
        for col in columns:
            self.production_tree.heading(col, text=col)
            self.production_tree.column(col, width=80)
        
        self.production_tree.pack(fill=tk.BOTH, expand=True)
        
        # 右側生產操作
        production_action_frame = ttk.LabelFrame(self.production_frame, text="生產操作", padding="10")
        production_action_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 開始生產按鈕
        start_prod_btn = ttk.Button(production_action_frame, text="開始生產", command=self.start_production)
        start_prod_btn.pack(fill=tk.X, pady=5)
        
        # 生產數量框架
        prod_qty_frame = ttk.Frame(production_action_frame)
        prod_qty_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(prod_qty_frame, text="生產數量:").pack(side=tk.LEFT)
        self.prod_qty_var = tk.StringVar(value="10")
        prod_qty_entry = ttk.Entry(prod_qty_frame, textvariable=self.prod_qty_var, width=8)
        prod_qty_entry.pack(side=tk.RIGHT)
        
        # 生產按鈕
        produce_btn = ttk.Button(production_action_frame, text="生產", command=self.produce)
        produce_btn.pack(fill=tk.X, pady=5)
        
        # 出貨按鈕
        ship_btn = ttk.Button(production_action_frame, text="出貨", command=self.ship_order)
        ship_btn.pack(fill=tk.X, pady=5)
        
        # 重新整理按鈕
        refresh_prod_btn = ttk.Button(production_action_frame, text="重新整理", command=self.refresh_production_list)
        refresh_prod_btn.pack(fill=tk.X, pady=5)
        
    def create_inventory_page(self):
        self.inventory_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.inventory_frame, text="庫存管理")
        
        # 庫存列表
        columns = ("產品", "庫存數量")
        self.inventory_tree = ttk.Treeview(self.inventory_frame, columns=columns, show="headings")
        
        # 設定欄位標題
        for col in columns:
            self.inventory_tree.heading(col, text=col)
            self.inventory_tree.column(col, width=150)
        
        self.inventory_tree.pack(fill=tk.BOTH, expand=True)
        
        # 重新整理按鈕
        refresh_inv_btn = ttk.Button(self.inventory_frame, text="重新整理", command=self.refresh_inventory)
        refresh_inv_btn.pack(pady=10)
        
    # 訂單管理功能
    def add_order_dialog(self):
        # 創建對話框
        dialog = tk.Toplevel(self.root)
        dialog.title("新增訂單")
        dialog.geometry("300x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 訂單資訊輸入
        ttk.Label(dialog, text="訂單編號:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        order_id_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=order_id_var).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(dialog, text="產品名稱:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        product_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=product_var).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(dialog, text="數量:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        quantity_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=quantity_var).grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(dialog, text="客戶:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        customer_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=customer_var).grid(row=3, column=1, padx=5, pady=5)
        
        # 確認按鈕
        def confirm():
            try:
                order_id = order_id_var.get()
                product = product_var.get()
                quantity = int(quantity_var.get())
                customer = customer_var.get()
                
                if not all([order_id, product, customer]):
                    messagebox.showerror("錯誤", "請填寫所有欄位")
                    return
                
                # 創建訂單
                order = Order(order_id, product, quantity, customer)
                self.production_manager.add_order(order)
                
                dialog.destroy()
                self.refresh_order_list()
            except ValueError:
                messagebox.showerror("錯誤", "數量必須是整數")
        
        ttk.Button(dialog, text="確認", command=confirm).grid(row=4, column=0, columnspan=2, pady=10)
        
    def show_order_details(self, event):
        item = self.order_tree.selection()[0]
        order_id = self.order_tree.item(item, "values")[0]
        
        # 獲取訂單詳細資訊
        order_info = self.production_manager.get_order_status(order_id)
        if not order_info:
            return
        
        # 顯示詳細資訊
        details = "\n".join([f"{k}: {v}" for k, v in order_info.items()])
        messagebox.showinfo(f"訂單 {order_id} 詳細資訊", details)
        
    def cancel_order(self):
        if not self.order_tree.selection():
            messagebox.showinfo("提示", "請先選擇一個訂單")
            return
            
        item = self.order_tree.selection()[0]
        order_id = self.order_tree.item(item, "values")[0]
        
        if messagebox.askyesno("確認", f"確定要取消訂單 {order_id} 嗎?"):
            result = self.production_manager.cancel_order(order_id)
            if result:
                messagebox.showinfo("成功", f"訂單 {order_id} 已取消")
                self.refresh_order_list()
                self.refresh_production_list()
            else:
                messagebox.showerror("錯誤", f"無法取消訂單 {order_id}")
    
    def refresh_order_list(self):
        # 清空現有列表
        for item in self.order_tree.get_children():
            self.order_tree.delete(item)
        
        # 獲取所有訂單
        orders = self.production_manager.get_all_orders()
        
        # 添加到列表
        for order in orders:
            values = (
                order["訂單編號"],
                order["產品"],
                order["數量"],
                order["客戶"],
                order["狀態"]
            )
            self.order_tree.insert("", tk.END, values=values)
    
    # 生產管理功能
    def start_production(self):
        if not self.production_tree.selection():
            messagebox.showinfo("提示", "請先選擇一個訂單")
            return
            
        item = self.production_tree.selection()[0]
        order_id = self.production_tree.item(item, "values")[0]
        
        result = self.production_manager.start_production(order_id)
        if result:
            messagebox.showinfo("成功", f"訂單 {order_id} 開始生產")
            self.refresh_production_list()
        else:
            messagebox.showerror("錯誤", f"無法開始生產訂單 {order_id}")
    
    def produce(self):
        if not self.production_tree.selection():
            messagebox.showinfo("提示", "請先選擇一個訂單")
            return
            
        item = self.production_tree.selection()[0]
        order_id = self.production_tree.item(item, "values")[0]
        
        try:
            quantity = int(self.prod_qty_var.get())
            if quantity <= 0:
                messagebox.showerror("錯誤", "生產數量必須大於0")
                return
                
            result = self.production_manager.produce(order_id, quantity)
            if result:
                messagebox.showinfo("成功", f"訂單 {order_id} 生產了 {quantity} 個產品")
                self.refresh_production_list()
                self.refresh_inventory()
            else:
                messagebox.showerror("錯誤", f"無法生產訂單 {order_id}")
        except ValueError:
            messagebox.showerror("錯誤", "生產數量必須是整數")
    
    def ship_order(self):
        if not self.production_tree.selection():
            messagebox.showinfo("提示", "請先選擇一個訂單")
            return
            
        item = self.production_tree.selection()[0]
        order_id = self.production_tree.item(item, "values")[0]
        
        result = self.production_manager.ship_order(order_id)
        if result:
            messagebox.showinfo("成功", f"訂單 {order_id} 已出貨")
            self.refresh_production_list()
            self.refresh_order_list()
            self.refresh_inventory()
        else:
            messagebox.showerror("錯誤", f"無法出貨訂單 {order_id}")
    
    def refresh_production_list(self):
        # 清空現有列表
        for item in self.production_tree.get_children():
            self.production_tree.delete(item)
        
        # 獲取所有訂單
        orders = self.production_manager.get_all_orders()
        
        # 添加到列表 (只顯示未完成的訂單)
        for order in orders:
            if order["狀態"] != "已出貨" and order["狀態"] != "已取消":
                # 獲取詳細資訊
                order_info = self.production_manager.get_order_status(order["訂單編號"])
                if order_info:
                    values = (
                        order["訂單編號"],
                        order["產品"],
                        order["數量"],
                        order["狀態"],
                        order_info["已生產數量"],
                        order_info["剩餘數量"]
                    )
                    self.production_tree.insert("", tk.END, values=values)
    
    # 庫存管理功能
    def refresh_inventory(self):
        # 清空現有列表
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)
        
        # 獲取所有庫存
        inventory = self.production_manager.check_inventory()
        
        # 添加到列表
        for product, info in inventory.items():
            self.inventory_tree.insert("", tk.END, values=(product, info["quantity"]))

# 主程式
# if __name__ == "__main__":
#     root = tk.Tk()
#     app = ProductionManagerGUI(root)
#     root.mainloop()
