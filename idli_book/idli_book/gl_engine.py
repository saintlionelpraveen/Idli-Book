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

			try:
				gle = frappe.new_doc("IB GL Entry")
				gle.update(entry)
				gle.transaction_type = doc.doctype
				gle.transaction_no = doc.name
				
				# Set posting date with fallback
				if hasattr(doc, 'posting_date') and doc.posting_date:
					gle.posting_date = doc.posting_date
				elif hasattr(doc, 'invoice_date') and doc.invoice_date:
					gle.posting_date = doc.invoice_date
				elif hasattr(doc, 'payment_date') and doc.payment_date:
					gle.posting_date = doc.payment_date
				elif hasattr(doc, 'bill_date') and doc.bill_date:
					gle.posting_date = doc.bill_date
				else:
					gle.posting_date = frappe.utils.today()
				
				gle.transaction_date = doc.creation
				gle.fiscal_year = GLEngine.get_fiscal_year(gle.posting_date)
				
				# Auto-populate against_account (contra accounts)
				if not gle.against_account:
					gle.against_account = GLEngine.get_against_accounts(gl_map, entry)
				
				# Auto-populate remarks if not provided
				if not gle.remarks:
					gle.remarks = GLEngine.generate_remarks(doc, entry)
				
				gle.insert(ignore_permissions=True)
				
			except Exception as e:
				frappe.log_error(f"GL Entry Creation Failed for {doc.doctype} {doc.name}", str(e))
				frappe.throw(f"Failed to create GL Entry: {str(e)}")
			
	@staticmethod
	def get_against_accounts(gl_map, current_entry):
		"""Get contra account(s) for an entry"""
		current_account = current_entry.get('account')
		is_debit = flt(current_entry.get('debit', 0)) > 0
		
		# Get opposite accounts (if this is debit, get all credit accounts and vice versa)
		contra_accounts = []
		for entry in gl_map:
			if entry.get('account') == current_account:
				continue
			
			# If current is debit, get credits; if current is credit, get debits
			if is_debit and flt(entry.get('credit', 0)) > 0:
				contra_accounts.append(entry.get('account'))
			elif not is_debit and flt(entry.get('debit', 0)) > 0:
				contra_accounts.append(entry.get('account'))
		
		return ", ".join(contra_accounts[:3]) if contra_accounts else ""
	
	@staticmethod
	def generate_remarks(doc, entry):
		"""Generate meaningful remarks based on document type"""
		doctype = doc.doctype
		doc_name = doc.name
		
		# Get party name if exists
		party_name = entry.get('party', '')
		
		# Generate contextual remarks
		if doctype == "IB Sales Invoice":
			base = f"Being sales to {party_name}" if party_name else "Being sales"
			return f"{base} vide {doc_name}"
		elif doctype == "IB Purchase Bill":
			base = f"Being purchase from {party_name}" if party_name else "Being purchase"
			return f"{base} vide {doc_name}"
		elif doctype == "IB Payment":
			payment_type = getattr(doc, 'payment_type', '')
			if payment_type == "Receive":
				return f"Being payment received from {party_name} vide {doc_name}" if party_name else f"Payment received vide {doc_name}"
			elif payment_type == "Pay":
				return f"Being payment made to {party_name} vide {doc_name}" if party_name else f"Payment made vide {doc_name}"
		
		# Default
		return entry.get('remarks', f"Entry for {doc_name}")
			
	@staticmethod
	def get_fiscal_year(date):
		date = frappe.utils.getdate(date)
		if date.month >= 4:
			return f"{date.year}-{date.year + 1}"
		else:
			return f"{date.year - 1}-{date.year}"
			
	@staticmethod
	def delete_gl_entries(doc):
		"""Mark GL entries as cancelled instead of deleting (audit trail)"""
		frappe.db.sql("""
			UPDATE `tabIB GL Entry`
			SET is_cancelled = 1
			WHERE transaction_type = %s AND transaction_no = %s
		""", (doc.doctype, doc.name))

