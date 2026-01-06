
import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate, add_days

class IBSalesInvoice(Document):
	def validate(self):
		self.set_dates()
		self.calculate_totals()
	
	def set_dates(self):
		if not self.invoice_date:
			self.invoice_date = nowdate()
			
		if not self.due_date and self.payment_terms:
			days = 0
			if self.payment_terms == "Net 15": days = 15
			elif self.payment_terms == "Net 30": days = 30
			elif self.payment_terms == "Net 45": days = 45
			elif self.payment_terms == "Net 60": days = 60
			self.due_date = add_days(self.invoice_date, days)

	def calculate_totals(self):
		subtotal = 0.0
		total_tax = 0.0
		
		for row in self.items:
			if not row.quantity: row.quantity = 0
			if not row.rate: row.rate = 0
			
			row.amount = flt(row.quantity) * flt(row.rate)
			
			row_net = row.amount
			row_tax = 0.0
			
			if self.is_tax_inclusive:
				if row.tax_rate:
					# Back-calculate net amount from inclusive
					row_net = row.amount / (1 + (row.tax_rate / 100))
					row_tax = row.amount - row_net
			else:
				if row.tax_rate:
					row_tax = row.amount * (row.tax_rate / 100)
			
			subtotal += row_net
			total_tax += row_tax
			
		self.subtotal = flt(subtotal)
		
		# Apply Discount on Subtotal
		self.discount_amount = flt(self.discount_amount)
		if self.discount_type == "Percentage":
			if self.discount_percentage:
				self.discount_amount = self.subtotal * (self.discount_percentage / 100)
			else:
				self.discount_amount = 0
		elif self.discount_type == "None":
			self.discount_amount = 0
			
		# Total Tax is just sum of line taxes for now
		# (Refinement: If discount applies before tax, tax should decrease. 
		# But usually GST is on transaction value. If discount is "Trade Discount" it reduces value.
		# For simplicity, let's assume discount reduces taxable value proportionally or just post-tax discount?
		# Zoho allows both "Discount before Tax" and "Discount after Tax".
		# Let's assume Discount is on Net Total (reducing taxable value) for simplicity and standardization.)
		
		# Pro-rating discount for tax reduction is complex. 
		# Let's keep it simple: Discount is post-calculation adjustment for now to avoid tax recalc complexity in this iteration,
		# unless we want to do it perfectly.
		# "Production Ready" implies handling it right.
		# If we discount the subtotal, the tax should essentially be recalculated strictly speaking if it's a value reduction.
		# Let's subtract discount from subtotal to get "Taxable Amount" generally.
		
		# Revised:
		# Taxable = Subtotal - Discount
		# Tax = Taxable * Rate? No, rate varies per item.
		# So Discount must be line-level or we pro-rate.
		# Simplest robust way: Discount Amount is treated as an expense or revenue reduction in GL, 
		# without altering line tax for now, OR we say Discount is "Post Tax" (Cash Discount).
		# Let's go with "Discount" as a separate GL Line (Debit Income or separate Expense).
		
		grand_total = self.subtotal - self.discount_amount + total_tax + flt(self.adjustment)
		self.tax_amount = total_tax
		self.grand_total = flt(grand_total)
		
		if self.status == "Draft":
			self.outstanding_amount = self.grand_total

	def on_submit(self):
		if self.outstanding_amount < 0: 
			frappe.throw("Outstanding amount cannot be negative")
			
		self.status = "Awaiting Payment"
		if not self.paid_amount:
			self.paid_amount = 0
			self.outstanding_amount = self.grand_total

		# Set posting_date for GL Engine
		self.posting_date = self.invoice_date

		self.make_gl_entries()
		self.update_stock(-1)
		# The following lines were incorrectly moved from on_cancel or make_gl_entries
		# from idli_book.idli_book.gl_engine import GLEngine
		# GLEngine.delete_gl_entries(self)

	def on_cancel(self):
		self.status = "Cancelled"
		self.update_stock(1)
		from idli_book.idli_book.gl_engine import GLEngine
		GLEngine.delete_gl_entries(self)

	def make_gl_entries(self):
		from idli_book.idli_book.gl_engine import GLEngine
		
		gl_entries = []
		org = frappe.get_doc("IB Organization", "IB Organization")
		
		# 1. Customer (Dr) = Grand Total
		customer_acct = frappe.db.get_value("IB Customer", self.customer, "default_receivable_account") or org.default_receivable_account
		gl_entries.append({
			"account": customer_acct,
			"party_type": "IB Customer",
			"party": self.customer,
			"debit": self.grand_total,
			"credit": 0,
			"remarks": "Invoice " + self.name
		})
		
		# 2. Income (Cr) = Subtotal (sum of line amounts after line discounts)
		for row in self.items:
			item_doc = frappe.get_doc("IB Item", row.item_code)
			income_acct = item_doc.default_income_account or org.default_income_account
			
			gl_entries.append({
				"account": income_acct,
				"debit": 0,
				"credit": row.amount or 0,
				"remarks": f"Income - {row.item_code}"
			})
		
		# 3. Tax (Cr) = Total Tax from line items
		if self.tax_amount > 0:
			# Use organization's default tax account or first tax liability account
			tax_acct = frappe.db.get_value("IB Chart of Accounts", {"account_type": "Tax"}, "name")
			if not tax_acct:
				tax_acct = org.default_expense_account  # Fallback
			
			gl_entries.append({
				"account": tax_acct,
				"debit": 0,
				"credit": self.tax_amount,
				"remarks": f"Tax on {self.name}"
			})

		# 4. Discount (Dr) - if header discount exists
		if self.discount_amount > 0:
			discount_acct = frappe.db.get_value("IB Chart of Accounts", {"account_name": "Discount Given"}, "name")
			if not discount_acct:
				discount_acct = org.default_expense_account
			
			gl_entries.append({
				"account": discount_acct,
				"debit": self.discount_amount,
				"credit": 0,
				"remarks": f"Discount on {self.name}"
			})

		# 5. Adjustment (Dr/Cr) - rounding
		if self.adjustment:
			round_off_acct = frappe.db.get_value("IB Chart of Accounts", {"account_name": "Round Off"}, "name")
			if not round_off_acct:
				round_off_acct = org.default_expense_account

			if self.adjustment > 0:
				gl_entries.append({
					"account": round_off_acct,
					"debit": 0,
					"credit": self.adjustment,
					"remarks": "Adjustment/Round Off"
				})
			else:
				gl_entries.append({
					"account": round_off_acct,
					"debit": abs(self.adjustment),
					"credit": 0,
					"remarks": "Adjustment/Round Off"
				})

		GLEngine.make_gl_entries(self, gl_entries)

	def update_stock(self, factor):
		for row in self.items:
			if frappe.db.get_value("IB Item", row.item_code, "track_inventory"):
				stock_qty = frappe.db.get_value("IB Item", row.item_code, "stock_quantity") or 0
				new_qty = flt(stock_qty) + (flt(row.quantity) * factor)
				frappe.db.set_value("IB Item", row.item_code, "stock_quantity", new_qty)
