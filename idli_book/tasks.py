# apps/idli_book/idli_book/tasks.py
import frappe
from frappe.utils import getdate, today
from frappe import enqueue

def daily_tasks():
    """Run daily automations: recurring invoices, due reminders, low stock alerts."""
    try:
        generate_recurring_invoices()
        send_due_reminders()
        low_stock_alerts()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "idli_book.daily_tasks")

def hourly_tasks():
    pass

def generate_recurring_invoices():
    docs = frappe.get_all("IB Invoice", filters={
        "is_recurring": 1,
        "next_recurring_date": getdate(today())
    }, fields=["name"])
    for d in docs:
        enqueue("idli_book.tasks.create_recurring_invoice", queue="short", kwargs={"docname": d.name})

def create_recurring_invoice(docname):
    doc = frappe.get_doc("IB Invoice", docname)
    new = frappe.copy_doc(doc, ignore_children=False)
    # new will have same name; convert to a new draft
    new.name = None
    new.posting_date = None
    new.status = "Draft"
    new.is_recurring = 0
    new.invoice_no = None
    new.insert()
    # compute next date for original
    next_date = _compute_next_date(doc.next_recurring_date, doc.recurring_interval)
    frappe.db.set_value("IB Invoice", docname, "next_recurring_date", next_date)
    # optionally auto-submit and email
    if doc.send_email:
        try:
            new.submit()
            frappe.sendmail(recipients=[doc.contact], subject=f"Invoice {new.name}", message=f"Invoice {new.name} created")
        except Exception:
            frappe.log_error(frappe.get_traceback(), "idli_book.create_recurring_invoice")

def _compute_next_date(current_date, interval):
    from frappe.utils import add_days, add_months, getdate
    d = getdate(current_date)
    if interval == "Weekly":
        return add_days(d, 7)
    if interval == "Monthly":
        return add_months(d, 1)
    if interval == "Yearly":
        return add_months(d, 12)
    return add_days(d, 30)

def send_due_reminders():
    docs = frappe.get_all("IB Invoice", filters={"status":"Submitted"}, fields=["name","contact","due_date","total"])
    for d in docs:
        if d.due_date and getdate(d.due_date) <= getdate(today()):
            enqueue("idli_book.tasks.send_reminder_email", queue="short", kwargs={"docname": d.name})

def send_reminder_email(docname):
    try:
        doc = frappe.get_doc("IB Invoice", docname)
        if doc.contact:
            frappe.sendmail(recipients=[doc.contact], subject=f"Payment Reminder for {doc.name}",
                            message=f"Your invoice {doc.name} is due. Amount: {doc.total}")
    except Exception:
        frappe.log_error(frappe.get_traceback(), "idli_book.send_reminder_email")

def low_stock_alerts():
    # Creates ToDo entries for items at or below reorder level and not already alerted today.
    items = frappe.get_all("IB Item", fields=["name", "item_name", "opening_stock", "low_stock"])
    for it in items:
        try:
            if it.low_stock is not None and it.opening_stock <= it.low_stock:
                # avoid duplicate todos within 1 day
                existing = frappe.get_all("ToDo", filters={
                    "description": ("like", f"%Low stock alert for {it.item_name}%")
                }, fields=["name"], limit_page_length=1)
                if not existing:
                    frappe.get_doc({
                        "doctype":"ToDo",
                        "description": f"Low stock alert for {it.item_name} ({it.name}) - current {it.opening_stock}",
                        "assigned_by": "Administrator",
                        "owner": "Administrator",
                        "status": "Open"
                    }).insert(ignore_permissions=True)
        except Exception:
            frappe.log_error(frappe.get_traceback(), "idli_book.low_stock_alerts")

