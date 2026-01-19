import frappe

def execute():
    """
    Reset account settings to defaults.
    Since accounts are now stored as Data fields,
    we just reset them to default values.
    """
    
    # Delete GL Entries if any
    gl_count = frappe.db.count("IB GL Entry")
    if gl_count > 0:
        print(f"Warning: Found {gl_count} GL Entries. Deleting them...")
        frappe.db.delete("IB GL Entry")
    
    # Reset Organization Account Defaults
    if frappe.db.exists("IB Organization", "IB Organization"):
        org = frappe.get_doc("IB Organization", "IB Organization")
        
        # Reset to default values
        org.default_receivable_account = "Accounts Receivable"
        org.default_payable_account = "Accounts Payable"
        org.default_income_account = "Sales Income"
        org.default_expense_account = "Operating Expenses"
        org.default_bank_account = "Bank Account"
        org.default_cash_account = "Cash"
        org.gst_output_account = "GST Payable"
        org.gst_input_account = "GST Input Credit"
        org.discount_account = "Discount Given"
        org.round_off_account = "Round Off"
        
        org.save(ignore_permissions=True)
        print("✅ Reset account defaults on IB Organization.")

    # Clear customer account overrides
    frappe.db.sql("""
        UPDATE `tabIB Customer` 
        SET default_receivable_account = NULL
    """)
    print("✅ Cleared customer account overrides.")
    
    # Clear vendor account overrides
    frappe.db.sql("""
        UPDATE `tabIB Vendor` 
        SET default_payable_account = NULL
    """)
    print("✅ Cleared vendor account overrides.")

    frappe.db.commit()
    print("✅ Account reset complete!")
