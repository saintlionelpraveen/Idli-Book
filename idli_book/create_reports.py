"""
Create all 14 IB Reports
Run with: bench execute idli_book.create_reports.create_all_reports
"""

import frappe
import json

def create_all_reports():
    """Create or update all 14 IB production reports"""
    
    reports_config = get_reports_config()
    
    created = 0
    updated = 0
    errors = 0
    
    for config in reports_config:
        try:
            # Delete if exists (clean slate)
            if frappe.db.exists("Report", config["name"]):
                frappe.delete_doc("Report", config["name"], force=1)
                print(f"🗑️  Deleted existing: {config['name']}")
            
            # Create new - WITHOUT roles in dict (causes error)
            doc = frappe.get_doc({
                "doctype": "Report",
                "report_name": config["name"],
                "ref_doctype": config["ref_doctype"],
                "report_type": "Query Report",
                "module": "Idli Book",
                "is_standard": "Yes",
                "query": config["query"],
                "filters": json.dumps(config["filters"]),
                "add_total_row": 1
            })
            
            doc.insert(ignore_permissions=True)
            created += 1
            print(f"✅ Created: {config['name']}")
            
        except Exception as e:
            errors += 1
            print(f"❌ Error with {config['name']}: {str(e)}")
            frappe.log_error(f"Report Creation Error: {config['name']}", str(e))
    
    frappe.db.commit()
    
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Created: {created}")
    print(f"  Updated: {updated}")
    print(f"  Errors: {errors}")
    print(f"{'='*60}")
    
    if created == 14:
        print("\n🎉 All 14 reports created successfully!")
    
    return {"created": created, "updated": updated, "errors": errors}


def get_reports_config():
    """Returns configuration for all 14 reports"""
    return [
        {
            "name": "IB Total Receivables",
            "ref_doctype": "IB Sales Invoice",
            "query": """SELECT 
    si.customer as "Customer:Link/IB Customer:180",
    si.customer_name as "Customer Name:Data:200",
    COUNT(DISTINCT si.name) as "Invoice Count:Int:100",
    SUM(si.outstanding_amount) as "Total Outstanding:Currency:150",
    SUM(CASE WHEN DATEDIFF(CURDATE(), si.invoice_date) <= 30 THEN si.outstanding_amount ELSE 0 END) as "0-30 Days:Currency:120",
    SUM(CASE WHEN DATEDIFF(CURDATE(), si.invoice_date) BETWEEN 31 AND 60 THEN si.outstanding_amount ELSE 0 END) as "31-60 Days:Currency:120",
    SUM(CASE WHEN DATEDIFF(CURDATE(), si.invoice_date) BETWEEN 61 AND 90 THEN si.outstanding_amount ELSE 0 END) as "61-90 Days:Currency:120",
    SUM(CASE WHEN DATEDIFF(CURDATE(), si.invoice_date) > 90 THEN si.outstanding_amount ELSE 0 END) as "90+ Days:Currency:120",
    ROUND(AVG(DATEDIFF(CURDATE(), si.invoice_date)), 0) as "Avg Days Outstanding:Int:120",
    MAX(si.invoice_date) as "Last Invoice Date:Date:120"
FROM `tabIB Sales Invoice` si
WHERE si.docstatus = 1 AND si.outstanding_amount > 0 
    AND si.invoice_date BETWEEN %(from_date)s AND %(to_date)s {conditions}
GROUP BY si.customer, si.customer_name
ORDER BY SUM(si.outstanding_amount) DESC""",
            "filters": [
                {"fieldname": "from_date", "label": "From Date", "fieldtype": "Date", "default": "frappe.datetime.add_months(frappe.datetime.nowdate(), -12)", "reqd": 1},
                {"fieldname": "to_date", "label": "To Date", "fieldtype": "Date", "default": "frappe.datetime.nowdate()", "reqd": 1},
                {"fieldname": "customer", "label": "Customer", "fieldtype": "Link", "options": "IB Customer"}
            ]
        },
        {
            "name": "IB Total Payables",
            "ref_doctype": "IB Purchase Bill",
            "query": """SELECT 
    pb.vendor as "Vendor:Link/IB Vendor:180",
    pb.vendor_name as "Vendor Name:Data:200",
    COUNT(DISTINCT pb.name) as "Bill Count:Int:100",
    SUM(pb.outstanding_amount) as "Total Payable:Currency:150",
    SUM(CASE WHEN pb.due_date < CURDATE() THEN pb.outstanding_amount ELSE 0 END) as "Overdue Amount:Currency:150",
    MIN(pb.due_date) as "Earliest Due Date:Date:120",
    MAX(pb.bill_date) as "Last Bill Date:Date:120"
FROM `tabIB Purchase Bill` pb
WHERE pb.docstatus = 1 AND pb.outstanding_amount > 0 
    AND pb.bill_date BETWEEN %(from_date)s AND %(to_date)s {conditions}
GROUP BY pb.vendor, pb.vendor_name
ORDER BY SUM(pb.outstanding_amount) DESC""",
            "filters": [
                {"fieldname": "from_date", "label": "From Date", "fieldtype": "Date", "default": "frappe.datetime.add_months(frappe.datetime.nowdate(), -12)", "reqd": 1},
                {"fieldname": "to_date", "label": "To Date", "fieldtype": "Date", "default": "frappe.datetime.nowdate()", "reqd": 1},
                {"fieldname": "vendor", "label": "Vendor", "fieldtype": "Link", "options": "IB Vendor"}
            ]
        },
        {
            "name": "IB Top 5 Expensive Purchases",
            "ref_doctype": "IB Item",
            "query": """SELECT 
    item.item as "Item:Link/IB Item:150",
    item.item_name as "Item Name:Data:200",
    MAX(item.rate) as "Highest Rate:Currency:120",
    SUM(item.qty) as "Total Qty Purchased:Float:120",
    SUM(item.amount) as "Total Amount:Currency:150",
    COUNT(DISTINCT bill.name) as "Purchase Count:Int:100",
    MAX(bill.bill_date) as "Last Purchase Date:Date:120"
FROM `tabIB Purchase Bill Item` item
INNER JOIN `tabIB Purchase Bill` bill ON item.parent = bill.name
WHERE bill.docstatus = 1 
    AND bill.bill_date BETWEEN %(from_date)s AND %(to_date)s {conditions}
GROUP BY item.item, item.item_name
ORDER BY MAX(item.rate) DESC
LIMIT 5""",
            "filters": [
                {"fieldname": "from_date", "label": "From Date", "fieldtype": "Date", "default": "frappe.datetime.add_months(frappe.datetime.nowdate(), -6)", "reqd": 1},
                {"fieldname": "to_date", "label": "To Date", "fieldtype": "Date", "default": "frappe.datetime.nowdate()", "reqd": 1}
            ]
        },
        {
            "name": "IB Inventory Count",
            "ref_doctype": "IB Item",
            "query": """SELECT 
    COALESCE(i.item_group, 'Uncategorized') as "Category:Data:150",
    COUNT(*) as "Item Count:Int:100",
    SUM(COALESCE(i.stock_qty, 0)) as "Total Stock Qty:Float:120",
    SUM(COALESCE(i.valuation_rate, 0) * COALESCE(i.stock_qty, 0)) as "Total Stock Value:Currency:150",
    SUM(CASE WHEN COALESCE(i.stock_qty, 0) > 0 THEN 1 ELSE 0 END) as "In Stock Count:Int:100",
    SUM(CASE WHEN COALESCE(i.stock_qty, 0) = 0 THEN 1 ELSE 0 END) as "Out of Stock Count:Int:100"
FROM `tabIB Item` i
WHERE i.track_inventory = 1 {conditions}
GROUP BY COALESCE(i.item_group, 'Uncategorized')
ORDER BY SUM(COALESCE(i.valuation_rate, 0) * COALESCE(i.stock_qty, 0)) DESC""",
            "filters": []
        },
        {
            "name": "IB Low Stock Alert",
            "ref_doctype": "IB Item",
            "query": """SELECT 
    i.name as "Item:Link/IB Item:150",
    i.item_name as "Item Name:Data:200",
    COALESCE(i.stock_qty, 0) as "Current Stock:Float:100",
    COALESCE(i.reorder_level, 0) as "Reorder Level:Float:100",
    (COALESCE(i.reorder_level, 0) - COALESCE(i.stock_qty, 0)) as "Shortage:Float:100",
    ROUND((COALESCE(i.stock_qty, 0) / NULLIF(COALESCE(i.reorder_level, 0), 0)) * 100, 1) as "Stock %:Percent:80",
    COALESCE(i.item_group, 'N/A') as "Item Group:Data:120",
    COALESCE(i.valuation_rate, 0) as "Valuation Rate:Currency:120"
FROM `tabIB Item` i
WHERE i.track_inventory = 1 
    AND COALESCE(i.stock_qty, 0) < COALESCE(i.reorder_level, 0)
    AND COALESCE(i.reorder_level, 0) > 0 {conditions}
ORDER BY (COALESCE(i.reorder_level, 0) - COALESCE(i.stock_qty, 0)) DESC""",
            "filters": []
        },
        {
            "name": "IB Vendor Summary",
            "ref_doctype": "IB Vendor",
            "query": """SELECT 
    v.name as "Vendor:Link/IB Vendor:180",
    v.vendor_name as "Vendor Name:Data:200",
    COUNT(DISTINCT pb.name) as "Bill Count:Int:80",
    SUM(CASE WHEN pb.docstatus = 1 THEN pb.grand_total ELSE 0 END) as "Total Purchase:Currency:150",
    SUM(CASE WHEN pb.docstatus = 1 THEN pb.outstanding_amount ELSE 0 END) as "Outstanding:Currency:130",
    MAX(pb.bill_date) as "Last Purchase:Date:110"
FROM `tabIB Vendor` v
LEFT JOIN `tabIB Purchase Bill` pb ON v.name = pb.vendor 
    AND pb.bill_date BETWEEN %(from_date)s AND %(to_date)s
WHERE 1=1 {conditions}
GROUP BY v.name, v.vendor_name
HAVING COUNT(DISTINCT pb.name) > 0
ORDER BY SUM(CASE WHEN pb.docstatus = 1 THEN pb.grand_total ELSE 0 END) DESC""",
            "filters": [
                {"fieldname": "from_date", "label": "From Date", "fieldtype": "Date", "default": "frappe.datetime.add_months(frappe.datetime.nowdate(), -12)", "reqd": 1},
                {"fieldname": "to_date", "label": "To Date", "fieldtype": "Date", "default": "frappe.datetime.nowdate()", "reqd": 1}
            ]
        },
        {
            "name": "IB Total Products Purchased",
            "ref_doctype": "IB Item",
            "query": """SELECT 
    item.item as "Item:Link/IB Item:150",
    item.item_name as "Item Name:Data:200",
    SUM(item.qty) as "Total Qty:Float:100",
    SUM(item.amount) as "Total Amount:Currency:150",
    COUNT(DISTINCT bill.name) as "Purchase Count:Int:100",
    AVG(item.rate) as "Avg Rate:Currency:120",
    MIN(bill.bill_date) as "First Purchase:Date:110",
    MAX(bill.bill_date) as "Last Purchase:Date:110"
FROM `tabIB Purchase Bill Item` item
INNER JOIN `tabIB Purchase Bill` bill ON item.parent = bill.name
WHERE bill.docstatus = 1 
    AND bill.bill_date BETWEEN %(from_date)s AND %(to_date)s {conditions}
GROUP BY item.item, item.item_name
ORDER BY SUM(item.amount) DESC""",
            "filters": [
                {"fieldname": "from_date", "label": "From Date", "fieldtype": "Date", "default": "frappe.datetime.add_months(frappe.datetime.nowdate(), -6)", "reqd": 1},
                {"fieldname": "to_date", "label": "To Date", "fieldtype": "Date", "default": "frappe.datetime.nowdate()", "reqd": 1}
            ]
        },
        {
            "name": "IB Purchase Bill Status",
            "ref_doctype": "IB Purchase Bill",
            "query": """SELECT 
    CASE 
        WHEN pb.docstatus = 0 THEN 'Draft'
        WHEN pb.docstatus = 1 THEN 'Submitted'
        WHEN pb.docstatus = 2 THEN 'Cancelled'
    END as "Status:Data:120",
    COUNT(*) as "Bill Count:Int:100",
    SUM(pb.grand_total) as "Total Amount:Currency:150",
    ROUND((COUNT(*) * 100.0 / (SELECT COUNT(*) FROM `tabIB Purchase Bill` WHERE bill_date BETWEEN %(from_date)s AND %(to_date)s)), 1) as "Percentage:Percent:100",
    SUM(CASE WHEN pb.docstatus = 1 THEN pb.outstanding_amount ELSE 0 END) as "Outstanding:Currency:130"
FROM `tabIB Purchase Bill` pb
WHERE pb.bill_date BETWEEN %(from_date)s AND %(to_date)s {conditions}
GROUP BY pb.docstatus
ORDER BY pb.docstatus""",
            "filters": [
                {"fieldname": "from_date", "label": "From Date", "fieldtype": "Date", "default": "frappe.datetime.add_months(frappe.datetime.nowdate(), -3)", "reqd": 1},
                {"fieldname": "to_date", "label": "To Date", "fieldtype": "Date", "default": "frappe.datetime.nowdate()", "reqd": 1}
            ]
        },
        {
            "name": "IB Amount Paid to Vendors",
            "ref_doctype": "IB Payment",
            "query": """SELECT 
    p.vendor as "Vendor:Link/IB Vendor:180",
    SUM(p.paid_amount) as "Total Paid:Currency:150",
    COUNT(*) as "Payment Count:Int:100",
    AVG(p.paid_amount) as "Avg Payment:Currency:130",
    MIN(p.payment_date) as "First Payment:Date:110",
    MAX(p.payment_date) as "Last Payment:Date:110"
FROM `tabIB Payment` p
WHERE p.payment_type = 'Pay' 
    AND p.docstatus = 1 
    AND p.payment_date BETWEEN %(from_date)s AND %(to_date)s {conditions}
GROUP BY p.vendor
ORDER BY SUM(p.paid_amount) DESC""",
            "filters": [
                {"fieldname": "from_date", "label": "From Date", "fieldtype": "Date", "default": "frappe.datetime.add_months(frappe.datetime.nowdate(), -6)", "reqd": 1},
                {"fieldname": "to_date", "label": "To Date", "fieldtype": "Date", "default": "frappe.datetime.nowdate()", "reqd": 1}
            ]
        },
        {
            "name": "IB Amount We Owe",
            "ref_doctype": "IB Purchase Bill",
            "query": """SELECT 
    pb.vendor as "Vendor:Link/IB Vendor:150",
    pb.name as "Bill No:Link/IB Purchase Bill:140",
    pb.bill_date as "Bill Date:Date:100",
    pb.due_date as "Due Date:Date:100",
    pb.outstanding_amount as "Outstanding:Currency:130",
    DATEDIFF(CURDATE(), pb.due_date) as "Days Overdue:Int:100",
    CASE 
        WHEN DATEDIFF(CURDATE(), pb.due_date) > 30 THEN 'High'
        WHEN DATEDIFF(CURDATE(), pb.due_date) > 0 THEN 'Medium'
        ELSE 'Normal'
    END as "Priority:Data:100"
FROM `tabIB Purchase Bill` pb
WHERE pb.docstatus = 1 AND pb.outstanding_amount > 0 {conditions}
ORDER BY DATEDIFF(CURDATE(), pb.due_date) DESC, pb.outstanding_amount DESC""",
            "filters": []
        },
        {
            "name": "IB Total Orders",
            "ref_doctype": "IB Sales Order",
            "query": """SELECT 
    CASE 
        WHEN so.docstatus = 0 THEN 'Draft'
        WHEN so.docstatus = 1 THEN 'Submitted'
        WHEN so.docstatus = 2 THEN 'Cancelled'
    END as "Status:Data:120",
    COUNT(*) as "Order Count:Int:100",
    SUM(so.grand_total) as "Total Value:Currency:150",
    SUM(CASE WHEN so.docstatus = 1 THEN so.outstanding_amount ELSE 0 END) as "Outstanding:Currency:130",
    COUNT(DISTINCT so.customer) as "Unique Customers:Int:120"
FROM `tabIB Sales Order` so
WHERE so.order_date BETWEEN %(from_date)s AND %(to_date)s {conditions}
GROUP BY so.docstatus
ORDER BY so.docstatus""",
            "filters": [
                {"fieldname": "from_date", "label": "From Date", "fieldtype": "Date", "default": "frappe.datetime.add_months(frappe.datetime.nowdate(), -3)", "reqd": 1},
                {"fieldname": "to_date", "label": "To Date", "fieldtype": "Date", "default": "frappe.datetime.nowdate()", "reqd": 1}
            ]
        },
        {
            "name": "IB Order Status",
            "ref_doctype": "IB Sales Order",
            "query": """SELECT 
    so.name as "Order No:Link/IB Sales Order:140",
    so.order_date as "Date:Date:100",
    so.customer as "Customer:Link/IB Customer:160",
    CASE 
        WHEN so.docstatus = 0 THEN 'Draft'
        WHEN so.docstatus = 1 THEN 'Submitted'
        WHEN so.docstatus = 2 THEN 'Cancelled'
    END as "Status:Data:100",
    so.grand_total as "Grand Total:Currency:130",
    so.outstanding_amount as "Outstanding:Currency:120"
FROM `tabIB Sales Order` so
WHERE so.order_date BETWEEN %(from_date)s AND %(to_date)s {conditions}
ORDER BY so.order_date DESC""",
            "filters": [
                {"fieldname": "from_date", "label": "From Date", "fieldtype": "Date", "default": "frappe.datetime.add_months(frappe.datetime.nowdate(), -3)", "reqd": 1},
                {"fieldname": "to_date", "label": "To Date", "fieldtype": "Date", "default": "frappe.datetime.nowdate()", "reqd": 1}
            ]
        },
        {
            "name": "IB Total Estimates",
            "ref_doctype": "IB Estimate",
            "query": """SELECT 
    CASE 
        WHEN e.docstatus = 0 THEN 'Draft'
        WHEN e.docstatus = 1 THEN 'Submitted'
        WHEN e.docstatus = 2 THEN 'Cancelled'
    END as "Status:Data:120",
    COUNT(*) as "Estimate Count:Int:110",
    SUM(e.grand_total) as "Total Value:Currency:150",
    SUM(CASE WHEN e.sales_order IS NOT NULL AND e.sales_order != '' THEN 1 ELSE 0 END) as "Converted to SO:Int:120",
    ROUND((SUM(CASE WHEN e.sales_order IS NOT NULL AND e.sales_order != '' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0)), 1) as "Conversion Rate:Percent:120"
FROM `tabIB Estimate` e
WHERE e.estimate_date BETWEEN %(from_date)s AND %(to_date)s {conditions}
GROUP BY e.docstatus
ORDER BY e.docstatus""",
            "filters": [
                {"fieldname": "from_date", "label": "From Date", "fieldtype": "Date", "default": "frappe.datetime.add_months(frappe.datetime.nowdate(), -3)", "reqd": 1},
                {"fieldname": "to_date", "label": "To Date", "fieldtype": "Date", "default": "frappe.datetime.nowdate()", "reqd": 1}
            ]
        },
        {
            "name": "IB Total Customers",
            "ref_doctype": "IB Customer",
            "query": """SELECT 
    c.name as "Customer:Link/IB Customer:160",
    c.customer_name as "Customer Name:Data:200",
    COUNT(DISTINCT si.name) as "Total Invoices:Int:110",
    SUM(CASE WHEN si.docstatus = 1 THEN si.grand_total ELSE 0 END) as "Total Revenue:Currency:150",
    SUM(CASE WHEN si.docstatus = 1 THEN si.outstanding_amount ELSE 0 END) as "Outstanding:Currency:130",
    MAX(si.invoice_date) as "Last Invoice Date:Date:120"
FROM `tabIB Customer` c
LEFT JOIN `tabIB Sales Invoice` si ON c.name = si.customer 
    AND si.invoice_date BETWEEN %(from_date)s AND %(to_date)s
WHERE si.name IS NOT NULL {conditions}
GROUP BY c.name, c.customer_name
ORDER BY SUM(CASE WHEN si.docstatus = 1 THEN si.grand_total ELSE 0 END) DESC""",
            "filters": [
                {"fieldname": "from_date", "label": "From Date", "fieldtype": "Date", "default": "frappe.datetime.add_months(frappe.datetime.nowdate(), -12)", "reqd": 1},
                {"fieldname": "to_date", "label": "To Date", "fieldtype": "Date", "default": "frappe.datetime.nowdate()", "reqd": 1}
            ]
        }
    ]
