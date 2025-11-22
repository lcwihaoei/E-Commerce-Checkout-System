"""
電商結帳系統 - Flask 後端 (E-commerce Checkout System - Flask Backend)
Baseline V3 + Feature Toggle for COD

Author: Professional Developer
Date: 2025-11-23
Version: 2.0 (with DevSecOps Feature Toggles)
"""

import json
import os
from flask import Flask, render_template, request, jsonify, abort

app = Flask(__name__)

# Mock 購物車資料 (Mock Cart Data)
# 商品總額: $170, 運費: $50 (固定), 總計: $220
mock_cart = {
    "subtotal": 170,
    "shipping_fee": 50,  # 固定運費，無免運邏輯
    "total": 220,        # 170 + 50
    "items": [           # 商品清單（目前僅用於後續擴充）
        {"name": "範例商品 (Sample Item)", "price": 170, "quantity": 1}
    ]
}


# ==================== Feature Toggle 管理 ====================
def load_toggles():
    """
    讀取 Feature Toggle 設定檔
    
    Returns:
        dict: Toggle 設定內容
        
    Security Note:
        - 使用快取避免每次請求都讀取檔案
        - 生產環境建議使用 Redis/Database 儲存 toggles
    """
    toggles_path = os.path.join(os.path.dirname(__file__), 'toggles.json')
    
    try:
        with open(toggles_path, 'r', encoding='utf-8') as f:
            toggles = json.load(f)
            return toggles
    except FileNotFoundError:
        # 若檔案不存在，返回預設值 (所有功能關閉)
        print(f"Warning: toggles.json not found at {toggles_path}")
        return {"enable_cod": False}
    except json.JSONDecodeError as e:
        # JSON 格式錯誤
        print(f"Error: Invalid JSON in toggles.json - {e}")
        return {"enable_cod": False}
    except Exception as e:
        # 其他錯誤
        print(f"Error loading toggles: {e}")
        return {"enable_cod": False}


@app.route('/')
def index():
    """
    首頁路由 - 渲染結帳選項頁面
    (Homepage route - Render checkout options page)
    
    Feature Toggle:
        - 讀取 enable_cod 狀態並傳遞至前端
    """
    toggles = load_toggles()
    return render_template('checkout.html', cart=mock_cart, enable_cod=toggles.get('enable_cod', False))


@app.route('/payment')
def payment():
    """
    付款頁面路由 - 渲染付款方式頁面
    (Payment route - Render payment method page)
    
    Feature Toggle:
        - 讀取 enable_cod 狀態並傳遞至前端
    """
    toggles = load_toggles()
    return render_template('payment.html', cart=mock_cart, enable_cod=toggles.get('enable_cod', False))


@app.route('/checkout', methods=['POST'])
def checkout():
    """
    結帳路由 - 處理結帳請求
    (Checkout route - Handle checkout request)
    
    Security Enhancement (DevSecOps):
        - 後端二次驗證 Feature Toggle 狀態
        - 防止前端被繞過後的惡意請求
    """
    try:
        # ========== 安全驗證：Feature Toggle 檢查 ==========
        toggles = load_toggles()
        enable_cod = toggles.get('enable_cod', False)
        
        # 取得付款方式
        payment_method = request.form.get('payment_method', 'credit_card')
        
        # 【重要】後端安全驗證：如果 COD 功能關閉，但使用者嘗試使用 COD
        if payment_method == 'cod' and not enable_cod:
            # 返回 403 Forbidden (功能未啟用)
            return jsonify({
                "status": "error",
                "message": "貨到付款功能目前未開放，請選擇其他付款方式",
                "error_code": "FEATURE_DISABLED"
            }), 403
        
        # ========== 原有的表單驗證邏輯 ==========
        # 取得表單資料 (Get form data)
        delivery_method = request.form.get('delivery_method', '宅配')
        invoice_type = request.form.get('invoice_type', '手機載具')
        
        # 根據付款方式進行不同的驗證
        if payment_method == 'credit_card':
            # 信用卡付款：驗證卡片資訊
            card_number = request.form.get('card_number')
            expiry_date = request.form.get('expiry_date')
            cvv = request.form.get('cvv')
            
            if not card_number or not expiry_date or not cvv:
                return jsonify({
                    "status": "error",
                    "message": "請填寫完整的信用卡資訊"
                }), 400
            
            payment_display = "信用卡"
        
        elif payment_method == 'cod':
            # 貨到付款：不需要卡片資訊
            payment_display = "貨到付款"
        
        else:
            # 未知付款方式
            return jsonify({
                "status": "error",
                "message": "無效的付款方式"
            }), 400
        
        # 模擬訂單成立 (Simulate order creation)
        order_data = {
            "order_id": "ORD-2025112300001",
            "total": mock_cart["total"],
            "payment_method": payment_display,
            "delivery_method": delivery_method,
            "invoice_type": invoice_type,
            "status": "已成立"
        }
        
        return jsonify({
            "status": "success",
            "message": "訂單已成功建立！",
            "order": order_data
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"系統錯誤: {str(e)}"
        }), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
