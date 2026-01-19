import frappe
from frappe import _

def setup_number_cards():
    cards = [
        {
            "name": "Total Invoices",
            "label": "Total Invoices",
            "type": "Document Count",
            "document_type": "Sales Invoice",
            "function": "Count",
            "is_standard": 1,
            "module": "Idli Book",
            "color": "#ECAD4B" 
        }
    ]

    for card in cards:
        if not frappe.db.exists("Number Card", card["name"]):
            doc = frappe.new_doc("Number Card")
            doc.update(card)
            doc.insert(ignore_permissions=True)
            print(f"Created Number Card: {card['name']}")
        else:
            print(f"Number Card {card['name']} already exists.")

    frappe.db.commit()

if __name__ == "__main__":
    setup_number_cards()
