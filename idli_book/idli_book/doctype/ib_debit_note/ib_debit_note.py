
import frappe
from frappe.model.document import Document
from frappe.utils import flt


class IBDebitNote(Document):
	def validate(self):
		self.calculate_totals()

	def calculate_totals(self):
		subtotal = 0.0
		total_tax = 0.0
		
		for row in self.items:
			if not row.qty: row.qty = 0
			if not row.rate: row.rate = 0
			row.amount = flt(row.qty) * flt(row.rate)
			
			row_net = row.amount
			row_tax = 0.0
			
			if self.is_tax_inclusive:
				if row.tax_percentage:
					row_net = row.amount / (1 + (row.tax_percentage / 100))
					row_tax = row.amount - row_net
			else:
				if row.tax_percentage:
					row_tax = row.amount * (row.tax_percentage / 100)
			
			subtotal += row_net
			total_tax += row_tax
			
		self.subtotal = flt(subtotal)
		self.tax_amount = flt(total_tax)
		self.grand_total = self.subtotal + self.tax_amount

	def on_submit(self):
		self.status = "Submitted"
		self.update_stock(-1)
		self.make_gl_entries()

	def on_cancel(self):
		self.status = "Cancelled"
		self.update_stock(1)
		from idli_book.idli_book.gl_engine import GLEngine
		GLEngine.delete_gl_entries(self)

	def make_gl_entries(self):
		from idli_book.idli_book.gl_engine import GLEngine
		gl_entries = []
		org = frappe.get_doc("IB Organization", "IB Organization")
		
		# 1. Debit Vendor
		vendor_acct = frappe.db.get_value("IB Vendor", self.vendor, "default_payable_account")
		if not vendor_acct:
			vendor_acct = org.default_payable_account
		
		gl_entries.append({
			"account": vendor_acct,
			"party_type": "IB Vendor",
			"party": self.vendor,
			"debit": self.grand_total,
			"credit": 0,
			"remarks": "Debit Note " + self.name
		})
		
		# 2. Credit Expense
		default_expense = org.default_expense_account
		
		for row in self.items:
			item_doc = frappe.get_doc("IB Item", row.item)
			expense_acct = getattr(item_doc, 'default_expense_account', None) or default_expense
			
			row_net = row.amount
			if self.is_tax_inclusive and row.tax_percentage:
				row_net = row.amount / (1 + (row.tax_percentage / 100))
			
			gl_entries.append({
				"account": expense_acct,
				"debit": 0,
				"credit": row_net,
				"remarks": "Return - " + row.item
			})
			
			# 3. Credit Tax
			if row_net < row.amount or (not self.is_tax_inclusive and row.tax_percentage):
				tax_val = 0
				if self.is_tax_inclusive:
					tax_val = row.amount - row_net
				else:
					tax_val = row_net * (row.tax_percentage / 100)
				
				tax_acct = org.gst_input_account
				gl_entries.append({
					"account": tax_acct,
					"debit": 0,
					"credit": tax_val,
					"remarks": "Tax Reversal - " + row.item
				})
				
		GLEngine.make_gl_entries(self, gl_entries)

	def update_stock(self, factor):
		for row in self.items:
			if frappe.db.get_value("IB Item", row.item, "track_inventory"):
				stock_qty = frappe.db.get_value("IB Item", row.item, "stock_quantity") or 0
				new_qty = flt(stock_qty) + (flt(row.qty) * factor)
				frappe.db.set_value("IB Item", row.item, "stock_quantity", new_qty)
