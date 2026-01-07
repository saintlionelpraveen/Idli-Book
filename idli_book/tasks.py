import frappe

def sync_email_statuses():
    """
    Cron Job: Syncs Email Queue status to [IB Estimate, IB Sales Order, IB Sales Invoice].
    Runs every few minutes.
    """
    doctypes = ["IB Estimate", "IB Sales Order", "IB Sales Invoice"]
    
    # Check Queued items in Email Queue
    # We look for ANY email sent recently that is linked to our doctypes
    
    for dt in doctypes:
        # Find documents that are 'Queued' locally but might be 'Sent' in Email Queue
        # Or generally just sync the latest status from Email Queue
        
        # Get emails from Queue linked to this doctype, updated in last 1 hour to be efficient
        email_queue_entries = frappe.db.sql(f"""
            SELECT reference_name, status 
            FROM `tabEmail Queue` 
            WHERE reference_doctype = '{dt}' 
            AND modified > DATE_SUB(NOW(), INTERVAL 24 HOUR)
            ORDER BY modified DESC
        """, as_dict=True)
        
        # We only care about the LATEST email for each doc
        latest_status = {}
        for entry in email_queue_entries:
            if entry.reference_name not in latest_status:
                latest_status[entry.reference_name] = entry.status
        
        # Update Doctype
        for docname, status in latest_status.items():
            mapped_status = "Queued"
            if status == "Sent": mapped_status = "Sent"
            elif status == "Error" or status == "Expired": mapped_status = "Error"
            
            # Check current and update if diff (Direct SQL for speed, no events)
            frappe.db.sql(f"""
                UPDATE `tab{dt}` 
                SET email_delivery_status = %s 
                WHERE name = %s AND email_delivery_status != %s
            """, (mapped_status, docname, mapped_status))
            
    frappe.db.commit()

def send_payment_reminders():
    """Run daily to send reminders for overdue invoices every 5 days"""
    from frappe.utils import today, date_diff, add_days
    
    current_date = today()
    
    # Get all invoices that are submitted but not fully paid
    invoices = frappe.get_all("IB Sales Invoice", 
        filters={
            "docstatus": 1,
            "status": ["in", ["Partially Paid", "Awaiting Payment", "Overdue"]],
            "outstanding_amount": [">", 0]
        }, 
        fields=["name", "customer", "due_date", "outstanding_amount", "grand_total"]
    )
    
    org_name = frappe.db.get_single_value('IB Organization', 'organization_name') or "Our Company"
    
    for inv in invoices:
        if not inv.due_date: continue
        
        # Calculate days overdue
        days_overdue = date_diff(current_date, inv.due_date)
        
        # Logic: Send reminder if it's strictly overdue (days > 0) AND multiple of 5
        if days_overdue > 0 and days_overdue % 5 == 0:
            
            customer_email = frappe.db.get_value("IB Customer", inv.customer, "email")
            if not customer_email: continue
            
            subject = f"Reminder: Invoice #{inv.name} is Overdue by {int(days_overdue)} Days"
            
            message = f"""
            <div style="font-family: Arial, sans-serif; padding: 20px;">
                <h3>Payment Reminder</h3>
                <p>Hello {inv.customer},</p>
                <p>This is a gentle reminder that payment for Invoice <b>#{inv.name}</b> was due on <b>{frappe.utils.formatdate(inv.due_date)}</b>.</p>
                
                <div style="background-color: #fff3cd; color: #856404; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 0;"><strong>Days Overdue:</strong> {int(days_overdue)}</p>
                    <p style="margin: 5px 0 0 0;"><strong>Outstanding Amount:</strong> {frappe.format(inv.outstanding_amount, {'fieldtype': 'Currency'})}</p>
                </div>
                
                <p>Please arrange for payment at your earliest convenience to avoid interruptions.</p>
                <p>If you have already made the payment, please disregard this email.</p>
                <br>
                <p>Best Regards,<br>{org_name}</p>
            </div>
            """
            
            try:
                frappe.sendmail(
                    recipients=customer_email,
                    subject=subject,
                    message=message,
                    reference_doctype="IB Sales Invoice",
                    reference_name=inv.name,
                    attachments=[frappe.attach_print("IB Sales Invoice", inv.name, print_format="Standard")]
                )
                frappe.log_error(f"Sent Reminder for {inv.name}", "Payment Reminder")
            except Exception as e:
                frappe.log_error(f"Failed Reminder for {inv.name}", str(e))
