"""
Script to update IB Item JSON with separate HSN/SAC fields
Run this in Frappe console
"""
import frappe
import json

def update_item_doctype():
    """Update IB Item doctype to have separate HSN and SAC fields"""
    
    # Get the doctype
    doc = frappe.get_doc("DocType", "IB Item")
    
    # Update field order
    field_order = [
        "item_details_tab",
        "item_type",
        "item_name",
        "sku",
        "unit",
        "hsn_code",  # NEW
        "sac_code",  # NEW
        "code_description",  # NEW - shows product name
        "tax_preference",
        "tax_percentage",
        "column_break_img",
        "item_image",
        "sales_info_section",
        "selling_price",
        "default_income_account",
        "sales_description",
        "column_break_sales",
        "is_sales_item",
        "purchase_info_section",
        "buying_price",
        "default_expense_account",
        "purchase_description",
        "column_break_buy",
        "is_purchase_item",
        "preferred_vendor",
        "inventory_section",
        "track_inventory",
        "inventory_account",
        "stock_quantity",
        "reorder_level",
        "column_break_inv",
        "opening_stock",
        "opening_stock_rate"
    ]
    
    doc.field_order = field_order
    
    # Remove old hsn_sac_code field
    doc.fields = [f for f in doc.fields if f.fieldname != "hsn_sac_code"]
    
    # Add new fields
    new_fields = [
        {
            "fieldname": "hsn_code",
            "fieldtype": "Data",
            "label": "HSN Code",
            "depends_on": "eval:doc.item_type=='Goods'",
            "length": 8,
            "description": "Enter HSN code - Product name and tax will auto-fill",
            "insert_after": "unit"
        },
        {
            "fieldname": "sac_code",
            "fieldtype": "Data",
            "label": "SAC Code",
            "depends_on": "eval:doc.item_type=='Service'",
            "length": 6,
            "description": "Enter SAC code - Service name and tax will auto-fill",
            "insert_after": "hsn_code"
        },
        {
            "fieldname": "code_description",
            "fieldtype": "Data",
            "label": "Code Description",
            "read_only": 1,
            "depends_on": "eval:doc.hsn_code || doc.sac_code",
            "description": "Auto-filled product/service description",
            "insert_after": "sac_code"
        }
    ]
    
    # Add fields
    for field_dict in new_fields:
        insert_after = field_dict.pop("insert_after", None)
        field = doc.append("fields", field_dict)
    
    # Make tax_percentage read-only
    for field in doc.fields:
        if field.fieldname == "tax_percentage":
            field.read_only = 1
            field.description = "Auto-filled from HSN/SAC code"
    
    # Save
    doc.save()
    frappe.db.commit()
    
    print("✅ IB Item doctype updated successfully!")
    print("📝 Run: bench migrate")
    
    return "Done"

# Run this function
# update_item_doctype()
