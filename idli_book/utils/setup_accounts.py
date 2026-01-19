import frappe

def execute():
    """
    Setup default account names for IB Organization.
    Since accounts are now stored as Data fields (not Links),
    we just set the standard account names.
    """
    
    # 1. Get or Create Organization
    org_name = "Idli Book"
    if not frappe.db.exists("IB Organization", "IB Organization"):
        org = frappe.new_doc("IB Organization")
        org.organization_name = org_name
        org.fiscal_year_start = "2025-04-01"
        org.base_currency = "INR"
    else:
        org = frappe.get_doc("IB Organization", "IB Organization")
        org_name = org.organization_name

    # 2. Set Standard Account Names (Data fields - no IB Chart of Accounts needed)
    print(f"Setting up account defaults for {org_name}...")
    
    # Receivable & Payable
    org.default_receivable_account = "Accounts Receivable"
    org.default_payable_account = "Accounts Payable"
    
    # Income & Expense
    org.default_income_account = "Sales Income"
    org.default_expense_account = "Operating Expenses"
    
    # Bank & Cash
    org.default_bank_account = "Bank Account"
    org.default_cash_account = "Cash"
    
    # Tax Accounts
    org.gst_output_account = "GST Payable"
    org.gst_input_account = "GST Input Credit"
    
    # Other Accounts
    org.discount_account = "Discount Given"
    org.round_off_account = "Round Off"
    
    org.save(ignore_permissions=True)
    print("✅ Set default account names on IB Organization.")

    frappe.db.commit()
    print("✅ Account setup complete!")
