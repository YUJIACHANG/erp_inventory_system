# ERP Inventory Management System

## Overview
This project is a Python-based ERP-style inventory, production, and sales management system with integrated reporting dashboards.  
It is designed to simulate real-world operational workflows commonly found in small and mid-sized manufacturing or trading companies.

The system combines data processing, visualization, and a GUI interface to support daily operational decision-making.

## Problem Motivation
In many real-world business environments, inventory, production, and shipment records are often managed through fragmented Excel files.  
This approach frequently leads to data inconsistency, low transparency, and inefficient decision-making.

This project addresses these issues by providing a centralized system that integrates:
- Inventory tracking and adjustment
- Production and inbound inventory records
- Sales order and shipment management
- Analytical dashboards for reporting and monitoring

## System Structure
ERP/
├── app/
│   ├── daily_report.py
│   ├── erp_tabs.py
│   ├── inventory_core.py
│   ├── production_gui.py
│   ├── production_manager.py
│   ├── report_module.py
│   └── sales_entry.py
├── assets/
│   ├── erp_icon.ico
│   ├── icon_daily.png
│   ├── icon_mfg.png
│   ├── icon_sales.png
│   └── icon_warehouse_out.png
├── initial_data/
│   ├── initial_inventory.xlsx
│   └── initial_order.xlsx
└── erp_main.py

## Key Features
- Inventory level tracking and manual adjustment
- Production entry and inbound inventory management
- Sales order and shipment processing
- Daily operational dashboard with visualized metrics
- Modular and extensible system architecture

## Technologies Used
- Python
- Tkinter (GUI)
- Pandas (data processing)
- Matplotlib (data visualization)
- Excel / JSON data handling

## How to Run
1. Ensure Python is installed (Python 3.7+ recommended).
2. Install required dependencies:
   pip install pandas matplotlib
3. Run the application:
   python ERP/erp_main.py
   
## What This Project Demonstrates
- End-to-end system design and integration
- Applied data processing and reporting
- Practical use of Python for operational decision support
- Experience with real-world data workflows and system-based projects

## Documentation
A detailed user operation manual is provided to demonstrate how the system is used in practice.  
The manual includes step-by-step workflows, GUI screenshots, and explanations of daily operations such as inventory initialization, production entry, order management, and analytical reporting.

Please refer to:
- `docs/User_Operation_Manual.pdf`
