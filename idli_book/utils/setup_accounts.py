import frappe

def execute():
    # 1. Get or Create Organization
    org_name = "Idli Book"
    if not frappe.db.exists("IB Organization", "IB Organization"):
        org = frappe.new_doc("IB Organization")
        org.organization_name = org_name
        org.fiscal_year_start = "2025-04-01"
        org.base_currency = "INR"
        org.save(ignore_permissions=True)
    else:
        org = frappe.get_doc("IB Organization", "IB Organization")
        org_name = org.organization_name

    # Helper function to create accounts
    def create_account(ac_type, ac_name, number):
        # Format: TYPE-/AC-{Org Name} -> Normalized
        safe_org = org_name.replace(" ", "-").upper()
        ac_id = f"{ac_type.upper()}-/AC-{safe_org}"
        
        if not frappe.db.exists("IB Chart of Accounts", ac_id):
            doc = frappe.new_doc("IB Chart of Accounts")
            doc.name = ac_id  # If autoname is set to Prompt or field:name
            doc.account_name = ac_name
            doc.account_number = number # Just in case
            doc.account_type = ac_type
            doc.is_group = 0
            doc.insert(ignore_permissions=True)
            print(f"Created: {ac_id}")
        else:
            print(f"Exists: {ac_id}")
        return ac_id

    # 2. Create Standard Accounts
    print(f"Setting up accounts for {org_name}...")
    
    # Asset
    receivable = create_account("Receivable", "Accounts Receivable", "1100")
    inventory = create_account("Stock", "Inventory Asset", "1200")
    bank = create_account("Bank", "Standard Bank", "1000")
    
    # Liability
    payable = create_account("Payable", "Accounts Payable", "2100")
    tax = create_account("Tax", "GST Payable", "2200")
    
    # Income
    sales = create_account("Income", "Sales Income", "4000")
    
    # Expense
    cogs = create_account("Expense", "Cost of Goods Sold", "5000")
    discount = create_account("Expense", "Discount Given", "5100")
    roundoff = create_account("Expense", "Round Off", "5200")
    
    # 3. Link to Organization
    org.default_receivable_account = receivable
    org.default_payable_account = payable
    org.default_income_account = sales
    org.default_expense_account = cogs
    org.save(ignore_permissions=True)
    print("Linked accounts to IB Organization.")

    # 4. Link to Customer defaults (Optional but good)
    customers = frappe.get_all("IB Customer")
    for c in customers:
        frappe.db.set_value("IB Customer", c.name, "default_receivable_account", receivable)
    
    # 5. Link Items default income (Optional)
    items = frappe.get_all("IB Item")
    for i in items:
        frappe.db.set_value("IB Item", i.name, "default_income_account", sales)
        frappe.db.set_value("IB Item", i.name, "default_expense_account", cogs)

    frappe.db.commit()
