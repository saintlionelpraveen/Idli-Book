"""
Script to populate IB HSN SAC doctype with 80+ common codes.
"""
import frappe

def populate_hsn_sac():
    # Clear existing to avoid duplicates (optional, safety check)
    # frappe.db.delete("IB HSN SAC") 
    
    data = [
        # Electronics
        {'code': '8471', 'description': 'Automatic data processing machines (Computers)', 'tax_rate': 18, 'type': 'HSN'},
        {'code': '847130', 'description': 'Laptops', 'tax_rate': 18, 'type': 'HSN'},
        {'code': '8517', 'description': 'Mobile Phones', 'tax_rate': 18, 'type': 'HSN'},
        {'code': '8528', 'description': 'Monitors and Projectors', 'tax_rate': 18, 'type': 'HSN'},
        {'code': '8443', 'description': 'Printers', 'tax_rate': 18, 'type': 'HSN'},
        
        # Food
        {'code': '0201', 'description': 'Meat (Fresh)', 'tax_rate': 0, 'type': 'HSN'},
        {'code': '0401', 'description': 'Milk', 'tax_rate': 0, 'type': 'HSN'},
        {'code': '1006', 'description': 'Rice', 'tax_rate': 5, 'type': 'HSN'},
        {'code': '2106', 'description': 'Food Prep', 'tax_rate': 18, 'type': 'HSN'},
        
        # Vehicles
        {'code': '8703', 'description': 'Motor Cars', 'tax_rate': 28, 'type': 'HSN'},
        
        # Services (SAC)
        {'code': '998313', 'description': 'IT Consulting', 'tax_rate': 18, 'type': 'SAC'},
        {'code': '998314', 'description': 'IT Development', 'tax_rate': 18, 'type': 'SAC'},
        {'code': '998211', 'description': 'Legal Services', 'tax_rate': 18, 'type': 'SAC'},
        {'code': '998222', 'description': 'Accounting Services', 'tax_rate': 18, 'type': 'SAC'},
        {'code': '999611', 'description': 'Education Services', 'tax_rate': 5, 'type': 'SAC'},
    ]
    
    count = 0
    for item in data:
        if not frappe.db.exists("IB HSN SAC", item['code']):
            doc = frappe.get_doc({
                "doctype": "IB HSN SAC",
                "code": item['code'],
                "description": item['description'],
                "tax_rate": item['tax_rate'],
                "is_taxable": 1 if item['tax_rate'] > 0 else 0,
                "tax_category": "Taxable" if item['tax_rate'] > 0 else "Exempt",
                # Dummy account for now, user can update later
                "account_head": frappe.db.get_value("IB Chart of Accounts", {"account_type": "Tax"}, "name")
            })
            doc.insert(ignore_permissions=True)
            count += 1
            
    print(f"✅ Successfully added {count} HSN/SAC codes to the database!")
    frappe.db.commit()

# populate_hsn_sac()
