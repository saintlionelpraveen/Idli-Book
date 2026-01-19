import frappe

def check_data():
    try:
        # Check IB Sales Order data
        print("--- Checking IB Sales Order Data ---")
        data = frappe.db.sql("""
            SELECT name, status, grand_total, docstatus 
            FROM `tabIB Sales Order` 
            ORDER BY creation DESC LIMIT 10
        """, as_dict=True)
        
        print(f"I found {len(data)} IB Sales Order records.")
        for row in data:
            print(f"Name: {row.name}, Status: {row.status}, Total: {row.grand_total}, DocStatus: {row.docstatus}")
            
    except Exception as e:
        print(f"Error executing query: {e}")

if __name__ == "__main__":
    check_data()
