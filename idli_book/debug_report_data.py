import frappe

def check_data():
    try:
        data = frappe.db.sql("SELECT name, status, grand_total FROM `tabSales Order` LIMIT 5", as_dict=True)
        print("Sales Orders found:", len(data))
        for row in data:
            print(row)
            
        if not data:
            print("No Sales Orders found in the database. Please create some Sales Orders to see data in the report.")
    except Exception as e:
        print(f"Error executing query: {e}")

if __name__ == "__main__":
    check_data()
