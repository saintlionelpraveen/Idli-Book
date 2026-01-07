"""
Quick diagnostic script to test GL Entry creation
Run with: bench --site site1.local console
Then: exec(open('test_gl.py').read())
"""

import frappe

def test_gl_creation():
    frappe.db.begin()
    
    try:
        # Test 1: Can we create a GL Entry manually?
        print("\n=== TEST 1: Manual GL Entry Creation ===")
        test_entry = frappe.new_doc("IB GL Entry")
        test_entry.posting_date = "2026-01-07"
        test_entry.transaction_type = "IB Sales Invoice"
        test_entry.transaction_no = "TEST-001"
        test_entry.account = "Sales Income"
        test_entry.debit = 1000
        test_entry.credit = 0
        test_entry.fiscal_year = "2025-2026"
        test_entry.insert(ignore_permissions=True)
        print(f"✅ Manual GL Entry Created: {test_entry.name}")
        
        # Test 2: Check recent invoices
        print("\n=== TEST 2: Recent Invoices ===")
        invoices = frappe.get_all("IB Sales Invoice",
            filters={"docstatus": 1},
            fields=["name", "invoice_date", "grand_total"],
            limit=3,
            order_by="creation desc"
        )
        
        for inv in invoices:
            print(f"\nInvoice: {inv.name}")
            print(f"  Date: {inv.invoice_date}")
            print(f"  Amount: {inv.grand_total}")
            
            # Check if GL entries exist
            gl_count = frappe.db.count("IB GL Entry", {
                "transaction_type": "IB Sales Invoice",
                "transaction_no": inv.name
            })
            print(f"  GL Entries: {gl_count}")
            
            if gl_count == 0:
                print(f"  ⚠️ Missing GL! Regenerating...")
                doc = frappe.get_doc("IB Sales Invoice", inv.name)
                doc.posting_date = doc.invoice_date
                doc.make_gl_entries()
                print(f"  ✅ GL Entries Created")
        
        frappe.db.commit()
        print("\n✅ Test Complete!")
        
    except Exception as e:
        frappe.db.rollback()
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_gl_creation()
