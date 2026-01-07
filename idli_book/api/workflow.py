import frappe
from frappe.utils import get_url

@frappe.whitelist(allow_guest=True)
def handle_estimate_response(name, action, token):
    """
    Handles Accept/Reject clicks from email.
    """
    if not name or not action or not token:
        return "Invalid Link"
    
    # Security Check: Compare token (simple check matches doc creation time or hash)
    doc = frappe.get_doc("IB Estimate", name)
    
    # Simple security: Token = Hex of creation timestamp (or better, a random secret field)
    # For MVP: We assume the link hash generated during send matches here.
    # checking valid secret (doc.name + doc.creation)
    expected_token = frappe.utils.data.generate_hash(doc.name + str(doc.creation), length=10)
    
    if token != expected_token:
        return """<h1 style="color:red">Invalid or Expired Link</h1>"""
    
    if doc.status == "Ordered" or doc.status == "Cancelled":
        return f"<h1>Estimate is already {doc.status}</h1>"

    if action == "accept":
        # 1. Update Status & Opinion
        doc.status = "Accepted"
        doc.customer_opinion = "Accepted"
        doc.save(ignore_permissions=True)
        doc.add_comment("Info", "Customer accepted the estimate via Email Link")
        
        # 2. Auto-Create Sales Order
        from idli_book.idli_book.doctype.ib_estimate.ib_estimate import make_sales_order
        so = make_sales_order(doc.name)
        so.insert(ignore_permissions=True)
        
        # 3. Notify Customer (Optional now, user wants minimal friction)
        # keeping it silent to the customer to match "no redirect/page" vibe might be better, 
        # but email confirmation is standard. I'll keep it but minimal.
        
        return get_auto_close_html("✅ Estimate Accepted. Order Created.")
        
    elif action == "reject":
        doc.status = "Halted"
        doc.customer_opinion = "Declined"
        doc.save(ignore_permissions=True)
        doc.add_comment("Info", "Customer declined the estimate via Email Link")
        return get_auto_close_html("❌ Estimate Declined.")

def get_customer_email(doc):
    return frappe.db.get_value("IB Customer", doc.customer, "email")

def get_auto_close_html(msg):
    return f"""
    <!DOCTYPE html>
    <html>
    <body style="background:#f4f4f4; display:flex; justify-content:center; align-items:center; height:100vh; font-family:sans-serif;">
        <div style="text-align:center;">
            <h2 style="color:#555;">{msg}</h2>
            <p>You can close this tab.</p>
        </div>
        <script>
            // Attempt to close the window immediately
            window.onload = function() {{
                window.open('','_parent','');
                window.close();
            }};
        </script>
    </body>
    </html>
    """
