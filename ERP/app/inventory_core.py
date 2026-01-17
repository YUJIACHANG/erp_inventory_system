import os
import pandas as pd
from typing import Dict, List, Optional, Union
import json
import logging
from datetime import datetime
import uuid

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("inventory_system.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("燈具庫存系統")

# # ==================== InventoryTransaction ====================
class InventoryTransaction:
    """庫存交易記錄類別，用於詳細記錄庫存的每次變動"""
    
    def __init__(self, product_name, transaction_type, quantity, order_id=None, notes=""):
        """初始化庫存交易記錄
        
        Args:
            product_name: 產品名稱
            transaction_type: 交易類型 ('in': 入庫, 'out': 出庫, 'adjust': 調整)
            quantity: 數量 (正數表示增加，負數表示減少)
            order_id: 訂單編號
            notes: 備註
        """
        self.transaction_id = str(uuid.uuid4())[:8]  # 生成短UUID作為交易ID
        self.timestamp = datetime.now()
        self.product_name = product_name
        self.transaction_type = transaction_type
        self.quantity = quantity
        self.order_id = order_id
        self.notes = notes
    
    def to_dict(self):
        """將交易記錄轉換為字典格式"""
        return {
            "TransactionID": self.transaction_id,
            "Timestamp": self.timestamp.isoformat(),
            "ProductName": self.product_name,
            "TransactionType": self.transaction_type,
            "Quantity": self.quantity,
            "OrderID": self.order_id,
            "Notes": self.notes
        }

# ==================== Inventory ====================
class Inventory:
    """庫存管理類別，處理產品庫存的增減與分析"""
    
    def __init__(self, database_path="working_data/inventory_data.json"):
        """初始化庫存管理"""
        self.products = {}  # 產品庫存資訊
        self.transactions = []  # 庫存交易記錄
        self.database_path = database_path
        self.alerts = []  # 庫存警報記錄
        
        # 若資料庫檔案存在，則載入資料
        self.load_data()
    
    def load_data(self):
        """從檔案中載入庫存資料"""
        if os.path.exists(self.database_path):
            try:
                with open(self.database_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.products = data.get('products', {})
                    
                    # 轉換交易記錄為物件
                    transactions_data = data.get('transactions', [])
                    self.transactions = []
                    for t in transactions_data:
                        transaction = InventoryTransaction(
                            t['ProductName'], 
                            t['TransactionType'], 
                            t['Quantity'], 
                            t.get('OrderID'), 
                            t.get('Notes', '')
                        )
                        transaction.transaction_id = t['TransactionID']
                        transaction.timestamp = datetime.fromisoformat(t['Timestamp'])
                        self.transactions.append(transaction)
                        
                print(f"已從 {self.database_path} 載入庫存資料")
            except Exception as e:
                print(f"載入庫存資料失敗: {str(e)}")
        else:
            print("庫存資料檔案不存在，將創建新的資料庫")
    

    
    def save_data(self):
        """將庫存資料保存到檔案"""
        try:
            data = {
                'products': self.products,
                'transactions': [t.to_dict() for t in self.transactions]
            }
            with open(self.database_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"庫存資料已保存到 {self.database_path}")
            return True
        except Exception as e:
            print(f"保存庫存資料失敗: {str(e)}")
            return False

    def add_product(self, product_name, initial_quantity=0, reorder_point=None, max_stock=None):
        """新增產品到庫存"""
        if product_name in self.products:
            print(f"產品 '{product_name}' 已經存在於庫存中")
            return False
            
        self.products[product_name] = {
            'quantity': initial_quantity,
            'reorder_point': reorder_point,
            'max_stock': max_stock,
            'last_stock_update': datetime.now().isoformat(),
            'created_date': datetime.now().isoformat()
        }
        
        # 保存資料
        self.save_data()
        print(f"產品 '{product_name}' 已新增到庫存，初始數量: {initial_quantity}")
        return True

    def add_alert(self, product_name, alert_type, message):
        """添加庫存警報"""
        alert = {
            'product_name': product_name,
            'alert_type': alert_type,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        self.alerts.append(alert)
        logger.warning(f"庫存警報: {message}")

    def get_product_info(self, name):
        """根據產品名稱獲取產品資訊"""
        if name in self.products:
            # 重建產品歷史記錄
            product_history = self.get_product_history(name)
            product_info = self.products[name].copy()
            product_info['history'] = product_history
            return product_info
        else:
            logger.warning(f"產品 '{name}' 不存在於庫存中")
            return None

    def get_product_history(self, product_name):
        """獲取產品的歷史記錄"""
        history = []
        for transaction in self.transactions:
            if transaction.product_name == product_name:
                history.append(transaction.to_dict())
        return history

    def stock_in(self, name, quantity, order_id=None, notes=""):
        """產品入庫"""
        if name not in self.products:
            logger.warning(f"產品 '{name}' 不存在於庫存中，將自動新增")
            self.add_product(name)
            
        self.products[name]['quantity'] += quantity
        self.products[name]['last_stock_update'] = datetime.now().isoformat()
        
        # 記錄交易
        transaction = InventoryTransaction(name, 'in', quantity, order_id, notes)
        self.transactions.append(transaction)
        
        # 檢查是否超過最大庫存量
        if self.products[name].get('max_stock') is not None and self.products[name]['quantity'] > self.products[name]['max_stock']:
            alert_msg = f"'{name}' 已超過最大庫存量 ({self.products[name]['max_stock']})"
            self.add_alert(name, "庫存過高", alert_msg)
        
        # 保存資料
        self.save_data()
        logger.info(f"'{name}' 入庫 {quantity} 個。目前庫存：{self.products[name]['quantity']}")
        return True

    def stock_out(self, name, quantity, order_id=None, notes=""):
        """產品出庫"""
        if name not in self.products:
            logger.warning(f"產品 '{name}' 不存在於庫存中")
            return False
            
        if self.products[name]['quantity'] >= quantity:
            self.products[name]['quantity'] -= quantity
            self.products[name]['last_stock_update'] = datetime.now().isoformat()
            
            # 記錄交易
            transaction = InventoryTransaction(name, 'out', quantity, order_id, notes)
            self.transactions.append(transaction)
            
            # 檢查是否低於再訂購點
            if self.products[name].get('reorder_point') is not None and self.products[name]['quantity'] <= self.products[name]['reorder_point']:
                alert_msg = f"'{name}' 庫存量 ({self.products[name]['quantity']}) 已低於再訂購點 ({self.products[name]['reorder_point']})"
                self.add_alert(name, "庫存過低", alert_msg)
            
            # 保存資料
            self.save_data()
            logger.info(f"'{name}' 出庫 {quantity} 個。目前庫存：{self.products[name]['quantity']}")
            return True
        else:
            logger.warning(f"'{name}' 庫存不足，無法出庫 {quantity} 個。目前庫存：{self.products[name]['quantity']}")
            return False


    def adjust_stock(self, name, new_quantity, notes=""):
        """調整庫存數量"""
        if name not in self.products:
            logger.warning(f"產品 '{name}' 不存在於庫存中")
            return False
            
        old_quantity = self.products[name]['quantity']
        adjustment = new_quantity - old_quantity
        
        self.products[name]['quantity'] = new_quantity
        self.products[name]['last_stock_update'] = datetime.now().isoformat()
        
        # 記錄交易
        transaction = InventoryTransaction(name, 'adjust', adjustment, None, notes)
        self.transactions.append(transaction)
        
        # 保存資料
        self.save_data()
        logger.info(f"'{name}' 庫存已調整，從 {old_quantity} 到 {new_quantity}")
        return True


    def set_reorder_point(self, name, reorder_point):
        """設定產品的再訂購點"""
        if name not in self.products:
            logger.warning(f"產品 '{name}' 不存在於庫存中")
            return False
            
        self.products[name]['reorder_point'] = reorder_point
        # 保存資料
        self.save_data()
        logger.info(f"'{name}' 的再訂購點已設定為 {reorder_point}")
        return True

    def set_max_stock(self, name, max_stock):
        """設定產品的最大庫存量"""
        if name not in self.products:
            logger.warning(f"產品 '{name}' 不存在於庫存中")
            return False
            
        self.products[name]['max_stock'] = max_stock
        # 保存資料
        self.save_data()
        logger.info(f"'{name}' 的最大庫存量已設定為 {max_stock}")
        return True


    def check_stocks(self):
        """檢查所有產品的庫存狀態"""
        return self.products


# ==================== Order ====================
class Order:
    """訂單類別，用於儲存和管理訂單資訊"""
    
    def __init__(self, trans_type: str, trans_id: str, seq_id: str,
                 prod_id: str, prod_name: str, quantity: int, price: float,
                 cust_id: str, cust_name: str, facto_id: str, facto_name: str,
                 trans_name: str = "銷貨單", submitted: datetime = None, priority: int = 1):
        """
        初始化訂單
        
        Args:
            trans_type: 單別代號
            trans_id: 單號
            seq_id: 序號
            prod_id: 品號
            prod_name: 品名
            quantity: 數量
            price: 單價
            cust_id: 客戶代號
            cust_name: 客戶名稱
            facto_id: 廠商代號
            facto_name: 廠商名稱
            trans_name: 單別名稱
            submitted: 提交時間
            priority: 訂單優先級 (1-5, 1為最高優先級)
        """
        self.trans_type = trans_type
        self.trans_id = trans_id
        self.seq_id = seq_id
        self.prod_id = prod_id
        self.prod_name = prod_name
        self.quantity = quantity
        self.price = price
        self.cust_id = cust_id
        self.cust_name = cust_name
        self.facto_id = facto_id
        self.facto_name = facto_name
        self.trans_name = trans_name
        self.submitted = submitted or datetime.now()
        self.priority = priority
        
        # 訂單狀態管理
        self.status = "待處理"  # 待處理、處理中、已完成、已取消、已送出
        self.created_time = datetime.now()
        self.updated_time = datetime.now()
        self.remarks = ""
        self.shipping_date = None
        self.produced_quantity = 0  # 已生產數量
        
    @property
    def amount(self) -> float:
        """計算訂單金額"""
        return self.quantity * self.price
    
    @property
    def order_key(self) -> str:
        """訂單唯一識別碼"""
        return f"{self.trans_id}-{self.seq_id}"
    
    def to_dict(self) -> Dict:
        """將訂單轉換為字典格式"""
        return {
            "單別": self.trans_type,
            "單號": self.trans_id,
            "序號": self.seq_id,
            "品號": self.prod_id,
            "品名": self.prod_name,
            "數量": self.quantity,
            "單價": self.price,
            "金額": self.amount,
            "客戶代號": self.cust_id,
            "客戶名稱": self.cust_name,
            "廠商代號": self.facto_id,
            "廠商名稱": self.facto_name,
            "單別名稱": self.trans_name,
            "提交時間": self.submitted,
            "狀態": self.status,
            "優先級": self.priority,
            "建立時間": self.created_time,
            "更新時間": self.updated_time,
            "備註": self.remarks,
            "出貨日期": self.shipping_date
        }
    

# ==================== ProductionManager ====================
class ProductionManager:
    """生產管理類別"""
    
    def __init__(self, inventory_system=None):
        """初始化生產管理系統
        
        Args:
            inventory_system: 庫存管理系統的實例，如果為None則創建新的
        """
        self.orders = {}  # 訂單清單，以 "訂單編號-序號" 為鍵
        self.inventory = inventory_system if inventory_system else Inventory()  # 庫存管理
    
    def add_order(self, order, preserve_status=False):
        """新增訂單
        
        Args:
            order: 訂單物件
            preserve_status: 是否保留原有狀態，True時不會強制設為「新訂單」
        """
        # 使用 訂單編號-序號 作為唯一識別 key
        order_key = order.order_key
        
        # 檢查是否已存在相同的訂單key
        if order_key in self.orders:
            print(f"警告：訂單 {order_key} 已存在，將被覆蓋")
        
        self.orders[order_key] = order
        
        # 只有在不保留狀態時才設為新訂單
        if not preserve_status:
            order.status = "新訂單"
        
        # 確保產品存在於庫存系統中
        if order.prod_name not in self.inventory.products:
            self.inventory.add_product(order.prod_name, initial_quantity=0)
            
        print(f"已新增訂單 {order_key}，產品：{order.prod_name}，數量：{order.quantity}，狀態：{order.status}")
        return order_key
    
    def get_order_by_trans_id(self, trans_id):
        """根據訂單編號獲取該訂單的所有序號項目"""
        matching_orders = []
        for order_key, order in self.orders.items():
            if order.trans_id == trans_id:
                matching_orders.append(order)
        return matching_orders
    
    def start_production(self, order_key):
        """開始生產訂單"""
        if order_key in self.orders:
            order = self.orders[order_key]
            if order.status == "新訂單":
                order.status = "生產中"
                order.production_date = datetime.now()
                print(f"訂單 {order_key} 開始生產，產品：{order.prod_name}，數量：{order.quantity}")
                return True
            else:
                print(f"訂單 {order_key} 狀態為 {order.status}，無法開始生產")
                return False
        else:
            print(f"找不到訂單 {order_key}")
            return False
    
    def produce(self, order_key, quantity):
        """生產一定數量的產品"""
        if order_key not in self.orders:
            print(f"訂單 {order_key} 不存在")
            return False
        
        order = self.orders[order_key]
        if order.status not in ["新訂單", "生產中"]:
            print(f"訂單 {order_key} 狀態為 {order.status}，無法生產")
            return False
        
        # 更新訂單狀態為生產中
        if order.status == "新訂單":
            order.status = "生產中"
            # 如果沒有設定生產日期，則設定為當前時間
            if not hasattr(order, 'production_date') or not order.production_date:
                order.production_date = datetime.now()
        
        # 計算實際生產數量
        remaining = order.quantity - order.produced_quantity
        actual_quantity = min(quantity, remaining)
        
        if actual_quantity <= 0:
            print(f"訂單 {order_key} 已經生產完成")
            return False
        
        # 更新生產數量
        order.produced_quantity += actual_quantity
        
        # 將生產的產品入庫
        self.inventory.stock_in(order.prod_name, actual_quantity, f"PROD-{order_key}")
        
        print(f"訂單 {order_key} 生產了 {actual_quantity} 個 {order.prod_name}，總共已生產 {order.produced_quantity} 個，剩餘 {order.quantity - order.produced_quantity} 個")
        
        # 檢查是否生產完成
        if order.produced_quantity >= order.quantity:
            order.status = "待出貨"
            # 設定生產完成日期
            if not hasattr(order, 'production_complete_date') or not order.production_complete_date:
                order.production_complete_date = datetime.now()
            print(f"訂單 {order_key} 生產完成，狀態更新為 {order.status}")
        
        return True
    
    def ship_order(self, order_key):
        """出貨訂單"""
        if order_key not in self.orders:
            print(f"訂單 {order_key} 不存在")
            return False
        
        order = self.orders[order_key]
        if order.status != "待出貨":
            print(f"訂單 {order_key} 狀態為 {order.status}，無法出貨")
            return False
        
        # 檢查庫存是否足夠
        inventory_info = self.inventory.get_product_info(order.prod_name)
        if not inventory_info or inventory_info["quantity"] < order.quantity:
            print(f"庫存不足，無法出貨。訂單需求: {order.quantity}，庫存: {inventory_info['quantity'] if inventory_info else 0}")
            return False
        
        # 從庫存中扣除產品
        result = self.inventory.stock_out(order.prod_name, order.quantity, f"SHIP-{order_key}")
        if not result:
            print(f"出貨失敗，無法從庫存中扣除產品")
            return False
        
        # 更新訂單狀態
        order.status = "已出貨"
        # 設定出貨日期
        if not hasattr(order, 'shipping_date') or not order.shipping_date:
            order.shipping_date = datetime.now()
        
        print(f"訂單 {order_key} 已出貨 {order.quantity} 個 {order.prod_name}")
        return True
    
    def get_order_status(self, order_key):
        """獲取訂單狀態
        
        Args:
            order_key: 訂單唯一識別碼 (訂單編號-序號)
            
        Returns:
            包含訂單狀態的字典，如果訂單不存在則返回None
        """
        if order_key not in self.orders:
            print(f"訂單 {order_key} 不存在")
            return None
        
        order = self.orders[order_key]
        
        # 計算生產進度
        progress = "0%"
        if order.quantity > 0:
            progress = f"{(order.produced_quantity / order.quantity * 100):.1f}%"
        
        status_info = {
            "訂單編號": order_key,
            "產品": order.prod_name,
            "數量": order.quantity,
            "訂單狀態": order.status,
            "生產進度": progress,
            "已生產數量": order.produced_quantity,
            "剩餘數量": order.quantity - order.produced_quantity,
            "狀態": order.status  
        }
        
        # 檢查是否有已分配量屬性
        if hasattr(order, 'allocated_quantity'):
            status_info["已分配量"] = order.allocated_quantity
        else:
            status_info["已分配量"] = 0
        
        # 添加日期資訊
        if hasattr(order, 'submitted') and order.submitted:
            status_info["訂單日期"] = order.submitted
        
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
        
        for order_key, order in self.orders.items():
            order_info = {
                "訂單編號": order_key,
                "產品": order.prod_name,
                "數量": order.quantity,
                "客戶": order.cust_name,
                "狀態": order.status
            }
            
            # 添加日期資訊
            if hasattr(order, 'submitted') and order.submitted:
                order_info["訂單日期"] = order.submitted.strftime('%Y-%m-%d')
            
            all_orders.append(order_info)
        
        return all_orders
    
    def cancel_order(self, order_key):
        """取消訂單
        
        Args:
            order_key: 訂單唯一識別碼 (訂單編號-序號)
            
        Returns:
            是否成功取消訂單
        """
        if order_key not in self.orders:
            print(f"訂單 {order_key} 不存在")
            return False
        
        order = self.orders[order_key]
        
        # 檢查訂單狀態，已出貨的訂單不能取消
        if order.status == "已出貨":
            print(f"訂單 {order_key} 已出貨，無法取消")
            return False
        
        # 如果訂單已經開始生產，需要處理已生產的產品
        if order.status == "生產中" and order.produced_quantity > 0:
            print(f"訂單 {order_key} 已生產 {order.produced_quantity} 個產品，這些產品將保留在庫存中")
        
        # 更新訂單狀態
        order.status = "已取消"
        print(f"訂單 {order_key} 已取消")
        
        return True
    
    def check_inventory(self):
        """檢查所有產品的庫存狀態
        
        Returns:
            包含所有產品庫存資訊的字典
        """
        return self.inventory.check_stocks()