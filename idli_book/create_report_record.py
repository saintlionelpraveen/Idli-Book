import frappe

def create_report():
    report_name = "IB Total Sales Order Status"
    if not frappe.db.exists("Report", report_name):
        doc = frappe.new_doc("Report")
        doc.report_name = report_name
        doc.report_type = "Script Report"
        doc.is_standard = "Yes"
        doc.module = "Idli Book"
        doc.ref_doctype = "Sales Order"
        doc.insert(ignore_permissions=True)
        print(f"Report '{report_name}' created successfully.")
    else:
        print(f"Report '{report_name}' already exists.")
    
    frappe.db.commit()

if __name__ == "__main__":
    create_report()
