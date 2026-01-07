import frappe

def execute():
    # Check for existing transactions first
    gl_count = frappe.db.count("IB GL Entry")
    if gl_count > 0:
        print(f"Warning: Found {gl_count} GL Entries. Deleting them first to allow Account deletion...")
        frappe.db.delete("IB GL Entry")
    
    # Delete all Accounts
    frappe.db.delete("IB Chart of Accounts")
    
    # Reset Organization Defaults to avoid broken links
    if frappe.db.exists("IB Organization", "IB Organization"):
        org = frappe.get_doc("IB Organization", "IB Organization")
        org.default_receivable_account = None
        org.default_payable_account = None
        org.default_income_account = None
        org.default_expense_account = None
        org.save(ignore_permissions=True)

    frappe.db.commit()
    print("✅ Successfully deleted all accounts from IB Chart of Accounts")
