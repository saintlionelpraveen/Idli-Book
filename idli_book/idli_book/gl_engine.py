import frappe
from frappe.utils import flt

class GLEngine:
	@staticmethod
	def make_gl_entries(doc, gl_map):
		"""
		gl_map = [
			{"account": "Acct Name", "debit": 100, "credit": 0, "party_type": "...", "party": "...", "remarks": "..."},
			...
		]
		"""
		# Validate Equality
		total_debit = sum(flt(e.get('debit', 0)) for e in gl_map)
		total_credit = sum(flt(e.get('credit', 0)) for e in gl_map)
		
		# Round off to avoid float issues
		total_debit = flt(total_debit, 2)
		total_credit = flt(total_credit, 2)

		if total_debit != total_credit:
			frappe.throw(f"Debit and Credit not equal. Debit: {total_debit}, Credit: {total_credit}")
		
		# Delete existing entries for this doc
		frappe.db.delete("IB GL Entry", {
			"transaction_type": doc.doctype,
			"transaction_no": doc.name
		})

		# Insert new entries
		for entry in gl_map:
			if flt(entry.get('debit', 0)) == 0 and flt(entry.get('credit', 0)) == 0:
				continue # Skip zero entries

			gle = frappe.new_doc("IB GL Entry")
			gle.update(entry)
			gle.transaction_type = doc.doctype
			gle.transaction_no = doc.name
			gle.posting_date = doc.posting_date
			gle.transaction_date = doc.creation
			gle.fiscal_year = GLEngine.get_fiscal_year(doc.posting_date)
			gle.insert(ignore_permissions=True)
			
	@staticmethod
	def get_fiscal_year(date):
		date = frappe.utils.getdate(date)
		if date.month >= 4:
			return f"{date.year}-{date.year + 1}"
		else:
			return f"{date.year - 1}-{date.year}"
			
	@staticmethod
	def delete_gl_entries(doc):
		frappe.db.delete("IB GL Entry", {
			"transaction_type": doc.doctype,
			"transaction_no": doc.name
		})

