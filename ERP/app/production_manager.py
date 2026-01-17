# production_manager.py

import pandas as pd
from datetime import datetime, timedelta

class ProductionManager:
    def __init__(self, inventory_system=None):
        """初始化生產管理系統
        
        Args:
            inventory_system: 庫存管理系統的實例，如果為None則創建新的
        """
        # from inventory import Inventory  # 從另一個模組導入
        
        self.orders = {}  # 訂單清單，以訂單ID為鍵
        # self.inventory = inventory_system if inventory_system else Inventory()  # 庫存管理
        self.inventory = inventory_system if inventory_system else DummyInventory()
    
    def add_order(self, order):
        """新增訂單"""
        self.orders[order.TransID] = order
        order.status = "新訂單"
        
        # 確保產品存在於庫存系統中
        if order.ProdName not in self.inventory.products:
            self.inventory.add_product(order.ProdName, initial_quantity=0)
            
        print(f"已新增訂單 {order.TransID}，產品：{order.ProdName}，數量：{order.Quantity}")
        return order.TransID
    
    def start_production(self, order_id):
        """開始生產訂單"""
        if order_id in self.orders:
            order = self.orders[order_id]
            if order.status == "新訂單":
                order.status = "生產中"
                order.production_date = datetime.now()
                print(f"訂單 {order_id} 開始生產，產品：{order.ProdName}，數量：{order.Quantity}")
                return True
            else:
                print(f"訂單 {order_id} 狀態為 {order.status}，無法開始生產")
                return False
        else:
            print(f"找不到訂單 {order_id}")
            return False
    
    def produce(self, order_id, quantity):
        """生產一定數量的產品"""
        if order_id not in self.orders:
            print(f"訂單 {order_id} 不存在")
            return False
        
        order = self.orders[order_id]
        if order.status not in ["新訂單", "生產中"]:
            print(f"訂單 {order_id} 狀態為 {order.status}，無法生產")
            return False
        
        # 更新訂單狀態為生產中
        if order.status == "新訂單":
            order.status = "生產中"
            # 如果沒有設定生產日期，則設定為當前時間
            if not hasattr(order, 'production_date') or not order.production_date:
                order.production_date = datetime.now()
        
        # 計算實際生產數量
        remaining = order.Quantity - order.produced_quantity
        actual_quantity = min(quantity, remaining)
        
        if actual_quantity <= 0:
            print(f"訂單 {order_id} 已經生產完成")
            return False
        
        # 更新生產數量
        order.produced_quantity += actual_quantity
        
        # 將生產的產品入庫
        self.inventory.stock_in(order.ProdName, actual_quantity, f"PROD-{order_id}")
        
        print(f"訂單 {order_id} 生產了 {actual_quantity} 個 {order.ProdName}，總共已生產 {order.produced_quantity} 個，剩餘 {order.Quantity - order.produced_quantity} 個")
        
        # 檢查是否生產完成
        if order.produced_quantity >= order.Quantity:
            order.status = "待出貨"
            # 設定生產完成日期
            if not hasattr(order, 'production_complete_date') or not order.production_complete_date:
                order.production_complete_date = datetime.now()
            print(f"訂單 {order_id} 生產完成，狀態更新為 {order.status}")
        
        return True
    
    def ship_order(self, order_id):
        """出貨訂單"""
        if order_id not in self.orders:
            print(f"訂單 {order_id} 不存在")
            return False
        
        order = self.orders[order_id]
        if order.status != "待出貨":
            print(f"訂單 {order_id} 狀態為 {order.status}，無法出貨")
            return False
        
        # 檢查庫存是否足夠
        inventory_info = self.inventory.get_product_info(order.ProdName)
        if not inventory_info or inventory_info["quantity"] < order.Quantity:
            print(f"庫存不足，無法出貨。訂單需求: {order.Quantity}，庫存: {inventory_info['quantity'] if inventory_info else 0}")
            return False
        
        # 從庫存中扣除產品
        result = self.inventory.stock_out(order.ProdName, order.Quantity, f"SHIP-{order_id}")
        if not result:
            print(f"出貨失敗，無法從庫存中扣除產品")
            return False
        
        # 更新訂單狀態
        order.status = "已出貨"
        # 設定出貨日期
        if not hasattr(order, 'shipping_date') or not order.shipping_date:
            order.shipping_date = datetime.now()
        
        print(f"訂單 {order_id} 已出貨 {order.Quantity} 個 {order.ProdName}")
        return True
    
    def get_order_status(self, order_id):
        """獲取訂單狀態
        
        Args:
            order_id: 訂單編號
            
        Returns:
            包含訂單狀態的字典，如果訂單不存在則返回None
        """
        if order_id not in self.orders:
            print(f"訂單 {order_id} 不存在")
            return None
        
        order = self.orders[order_id]
        
        # 計算生產進度
        progress = "0%"
        if order.Quantity > 0:
            progress = f"{(order.produced_quantity / order.Quantity * 100):.1f}%"
        
        status_info = {
            "訂單編號": order_id,
            "產品": order.ProdName,
            "數量": order.Quantity,
            "訂單狀態": order.status,
            "生產進度": progress,
            "已生產數量": order.produced_quantity,
            "剩餘數量": order.Quantity - order.produced_quantity
        }
        
        # 添加日期資訊（如果有）
        if hasattr(order, 'order_date') and order.order_date:
            status_info["訂單日期"] = order.order_date
        
        if hasattr(order, 'production_date') and order.production_date:
            status_info["生產開始日期"] = order.production_date
        
        if hasattr(order, 'production_complete_date') and order.production_complete_date:
            status_info["生產完成日期"] = order.production_complete_date
        
        if hasattr(order, 'shipping_date') and order.shipping_date:
            status_info["出貨日期"] = order.shipping_date
        
        return status_info
    
    def get_all_orders(self):
        """獲取所有訂單的基本資訊
        
        Returns:
            包含所有訂單基本資訊的列表
        """
        all_orders = []
        
        for order_id, order in self.orders.items():
            order_info = {
                "訂單編號": order_id,
                "產品": order.ProdName,
                "數量": order.Quantity,
                "客戶": order.CustName,
                "狀態": order.status
            }
            
            # 添加日期資訊（如果有）
            if hasattr(order, 'order_date') and order.order_date:
                order_info["訂單日期"] = order.order_date.strftime('%Y-%m-%d')
            
            all_orders.append(order_info)
        
        return all_orders
    
    def cancel_order(self, order_id):
        """取消訂單
        
        Args:
            order_id: 訂單編號
            
        Returns:
            是否成功取消訂單
        """
        if order_id not in self.orders:
            print(f"訂單 {order_id} 不存在")
            return False
        
        order = self.orders[order_id]
        
        # 檢查訂單狀態，已出貨的訂單不能取消
        if order.status == "已出貨":
            print(f"訂單 {order_id} 已出貨，無法取消")
            return False
        
        # 如果訂單已經開始生產，需要處理已生產的產品
        if order.status == "生產中" and order.produced_quantity > 0:
            print(f"訂單 {order_id} 已生產 {order.produced_quantity} 個產品，這些產品將保留在庫存中")
        
        # 更新訂單狀態
        order.status = "已取消"
        print(f"訂單 {order_id} 已取消")
        
        return True
    
    def check_inventory(self):
        """檢查所有產品的庫存狀態
        
        Returns:
            包含所有產品庫存資訊的字典
        """
        return self.inventory.check_stocks()


# 替代庫存系統（避免缺少 inventory.py 報錯）
class DummyInventory:
    def __init__(self):
        self.products = {}

    def add_product(self, name, initial_quantity=0):
        self.products[name] = {"quantity": initial_quantity}

    def stock_in(self, name, qty, note):
        if name not in self.products:
            self.add_product(name)
        self.products[name]["quantity"] += qty

    def stock_out(self, name, qty, note):
        if name in self.products and self.products[name]["quantity"] >= qty:
            self.products[name]["quantity"] -= qty
            return True
        return False

    def get_product_info(self, name):
        return self.products.get(name, {"quantity": 0})

    def check_stocks(self):
        return {name: {"quantity": info["quantity"]} for name, info in self.products.items()}