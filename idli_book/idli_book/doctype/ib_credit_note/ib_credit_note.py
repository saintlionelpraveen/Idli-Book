
import frappe
from frappe.model.document import Document
from frappe.utils import flt


class IBCreditNote(Document):
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
		self.update_stock(1)
		self.make_gl_entries()

	def on_cancel(self):
		self.status = "Cancelled"
		self.update_stock(-1)
		from idli_book.idli_book.gl_engine import GLEngine
		GLEngine.delete_gl_entries(self)

	def make_gl_entries(self):
		from idli_book.idli_book.gl_engine import GLEngine
		gl_entries = []
		org = frappe.get_doc("IB Organization", "IB Organization")
		
		# 1. Credit Customer
		customer_acct = frappe.db.get_value("IB Customer", self.customer, "default_receivable_account")
		if not customer_acct:
			customer_acct = org.default_receivable_account
		
		gl_entries.append({
			"account": customer_acct,
			"party_type": "IB Customer",
			"party": self.customer,
			"debit": 0,
			"credit": self.grand_total,
			"remarks": "Credit Note " + self.name
		})
		
		# 2. Debit Income
		default_income = org.default_income_account
		
		for row in self.items:
			item_doc = frappe.get_doc("IB Item", row.item)
			income_acct = getattr(item_doc, 'default_income_account', None) or default_income
			
			row_net = row.amount
			if self.is_tax_inclusive and row.tax_percentage:
				row_net = row.amount / (1 + (row.tax_percentage / 100))
			
			gl_entries.append({
				"account": income_acct,
				"debit": row_net,
				"credit": 0,
				"remarks": "Return - " + row.item
			})
			
			# 3. Debit Tax
			if row_net < row.amount or (not self.is_tax_inclusive and row.tax_percentage):
				tax_val = 0
				if self.is_tax_inclusive:
					tax_val = row.amount - row_net
				else:
					tax_val = row_net * (row.tax_percentage / 100)
				
				tax_acct = org.gst_output_account
				gl_entries.append({
					"account": tax_acct,
					"debit": tax_val,
					"credit": 0,
					"remarks": "Tax Reversal - " + row.item
				})
				
		GLEngine.make_gl_entries(self, gl_entries)

	def update_stock(self, factor):
		for row in self.items:
			if frappe.db.get_value("IB Item", row.item, "track_inventory"):
				stock_qty = frappe.db.get_value("IB Item", row.item, "stock_quantity") or 0
				new_qty = flt(stock_qty) + (flt(row.qty) * factor)
				frappe.db.set_value("IB Item", row.item, "stock_quantity", new_qty)
