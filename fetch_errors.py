
import frappe

def get_latest_errors():
    errors = frappe.get_all("Error Log", fields=["method", "error", "creation"], order_by="creation desc", limit=5)
    for err in errors:
        print(f"--- Error at {err.creation} ---")
        print(f"Method: {err.method}")
        print(f"Traceback:\n{err.error}\n")

if __name__ == "__main__":
    frappe.connect()
    get_latest_errors()
