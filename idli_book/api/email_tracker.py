import frappe

def update_estimate_email_status(doc, method):
    """
    Linked to Email Queue on_update.
    Syncs the Email Queue status back to IB Estimate, Sales Order, Sales Invoice.
    """
    valid_doctypes = ["IB Estimate", "IB Sales Order", "IB Sales Invoice"]
    
    if doc.reference_doctype in valid_doctypes and doc.reference_name:
        # Exact Mapping
        status_map = {
            "Not Sent": "Not Sent",
            "Sending": "Queued",
            "Sent": "Sent",
            "Error": "Error",
            "Expired": "Error"
        }
        
        email_status = doc.status
        new_est_status = status_map.get(email_status, "Queued")
        
        # Check current status
        current_status = frappe.db.get_value(doc.reference_doctype, doc.reference_name, "email_delivery_status")
        
        if current_status != new_est_status:
           # Silent Update
           frappe.db.set_value(doc.reference_doctype, doc.reference_name, "email_delivery_status", new_est_status)
           frappe.db.commit()
