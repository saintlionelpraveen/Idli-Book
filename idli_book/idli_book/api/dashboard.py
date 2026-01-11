import frappe
from frappe.utils import fmt_money

@frappe.whitelist()
def get_top_expense_items(filters=None):
    """
    Get top 5 most expensive items purchased (by rate)
    Shows item name and purchase price
    
    Returns:
        dict: Contains HTML formatted list of top 5 expensive items
    """
    try:
        # Try Purchase Bill Items first (if exists)
        items = get_expensive_from_purchase_bills()
        
        # Fallback to Sales Invoice Items if Purchase Bills don't exist
        if not items:
            items = get_expensive_from_sales_invoices()
        
        # Fallback to Sales Order Items
        if not items:
            items = get_expensive_from_sales_orders()
        
        if items and len(items) > 0:
            # Format as HTML list
            html_list = "<div style='text-align: left; font-size: 12px;'>"
            
            for idx, item in enumerate(items[:5], 1):
                item_name = item.get('item_name') or item.get('item') or 'Unknown'
                rate = item.get('rate') or 0
                
                html_list += f"""
                <div style='padding: 4px 0; border-bottom: 1px solid #eee;'>
                    <strong>{idx}. {item_name}</strong><br/>
                    <span style='color: #e74c3c; font-size: 13px;'>₹ {fmt_money(rate, 0, 'INR')}</span>
                </div>
                """
            
            html_list += "</div>"
            
            # Return highest price as value
            return {
                "value": items[0].get('rate', 0),
                "label": html_list
            }
            
    except Exception as e:
        frappe.log_error(f"Error in get_top_expense_items: {str(e)}", "Dashboard Number Card Error")
    
    # Ultimate fallback
    return {
        "value": 0,
        "label": "<div style='color: #999;'>No purchase data available</div>"
    }

# Backward compatibility alias
get_top_expense_item = get_top_expense_items


def get_expensive_from_purchase_bills():
    """Get expensive items from Purchase Bills"""
    try:
        return frappe.db.sql("""
            SELECT 
                item.item,
                item.item_name,
                MAX(item.rate) as rate
            FROM `tabIB Purchase Bill Item` item
            INNER JOIN `tabIB Purchase Bill` bill 
                ON item.parent = bill.name
            WHERE bill.docstatus = 1
            GROUP BY item.item, item.item_name
            ORDER BY rate DESC
            LIMIT 5
        """, as_dict=True)
    except:
        return None


def get_expensive_from_sales_invoices():
    """Get expensive items from Sales Invoices (fallback)"""
    try:
        return frappe.db.sql("""
            SELECT 
                item.item,
                item.item_name,
                MAX(item.rate) as rate
            FROM `tabIB Sales Invoice Item` item
            INNER JOIN `tabIB Sales Invoice` invoice 
                ON item.parent = invoice.name
            WHERE invoice.docstatus = 1
            GROUP BY item.item, item.item_name
            ORDER BY rate DESC
            LIMIT 5
        """, as_dict=True)
    except:
        return None


def get_expensive_from_sales_orders():
    """Get expensive items from Sales Orders (fallback)"""
    try:
        return frappe.db.sql("""
            SELECT 
                item.item,
                item.item_name,
                MAX(item.rate) as rate
            FROM `tabIB Sales Order Item` item
            INNER JOIN `tabIB Sales Order` so 
                ON item.parent = so.name
            WHERE so.docstatus = 1
            GROUP BY item.item, item.item_name
            ORDER BY rate DESC
            LIMIT 5
        """, as_dict=True)
    except:
        return None
