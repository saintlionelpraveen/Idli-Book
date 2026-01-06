import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate

class IBPurchaseBill(Document):
	def validate(self):
		self.calculate_totals()
	
	def calculate_totals(self):
		"""Calculate totals"""
		subtotal = 0.0
		total_tax = 0.0
		
		for row in self.items:
			if not row.qty:
				row.qty = 0
			if not row.rate:
				row.rate = 0
			
			# Calculate line amount
			row.amount = flt(row.qty) * flt(row.rate)
			
			# Calculate tax if applicable
			row_tax = 0.0
			if row.tax_percentage:
				row_tax = row.amount * (row.tax_percentage / 100)
			
			subtotal += row.amount
			total_tax += row_tax
		
		self.subtotal = flt(subtotal)
		self.tax_amount = flt(total_tax)
		
		# Apply discount
		discount = 0
		if self.discount_type == "Percentage" and self.discount_percentage:
			discount = subtotal * (self.discount_percentage / 100)
		elif self.discount_type == "Amount" and self.discount_amount:
			discount = self.discount_amount
		
		# Calculate grand total
		self.grand_total = flt(self.subtotal + self.tax_amount - discount + flt(self.adjustment or 0))
		
		# Set outstanding if new
		if not self.paid_amount:
			self.paid_amount = 0
		self.outstanding_amount = self.grand_total - self.paid_amount
	
	def on_submit(self):
		self.status = "Awaiting Payment"
		self.outstanding_amount = self.grand_total
		self.update_stock(factor=1)
		self.make_gl_entries()
		self.update_purchase_order_status()
	
	def on_cancel(self):
		from idli_book.idli_book.gl_engine import GLEngine
		GLEngine.delete_gl_entries(self)
		self.update_stock(factor=-1)
	
	def update_stock(self, factor):
		"""Update inventory stock quantities"""
		for row in self.items:
			# Check if item tracks inventory
			track_inventory = frappe.db.get_value("IB Item", row.item, "track_inventory")
			if track_inventory:
				current_qty = frappe.db.get_value("IB Item", row.item, "stock_quantity") or 0
				new_qty = current_qty + (flt(row.qty) * factor)
				frappe.db.set_value("IB Item", row.item, "stock_quantity", new_qty)
	
	def make_gl_entries(self):
		"""Create GL entries for purchase bill"""
		from idli_book.idli_book.gl_engine import GLEngine
		
		gl_entries = []
		org = frappe.get_doc("IB Organization", "IB Organization")
		
		# Calculate total expense (subtotal after discount)
		total_expense = self.subtotal
		
		# Apply discount to expense
		if self.discount_type == "Percentage" and self.discount_percentage:
			total_expense = total_expense - (total_expense * (self.discount_percentage / 100))
		elif self.discount_type == "Amount" and self.discount_amount:
			total_expense = total_expense - self.discount_amount
		
		# 1. Debit Expense account (subtotal - discount)
		expense_account = org.default_expense_account if hasattr(org, 'default_expense_account') else None
		
		# Fallback: Find or create expense account
		if not expense_account:
			expense_account = frappe.db.get_value("IB Chart of Accounts", {"account_type": "Expense"})
		
		if not expense_account:
			# Auto-create default expense account
			expense_doc = frappe.get_doc({
				"doctype": "IB Chart of Accounts",
				"account_name": "Purchase Expense - Organization",
				"account_type": "Expense",
				"root_type": "Expense",
				"is_group": 0
			})
			expense_doc.insert(ignore_permissions=True)
			frappe.db.commit()
			expense_account = expense_doc.name
		
		gl_entries.append({
			"account": expense_account,
			"debit": flt(total_expense),
			"credit": 0,
			"remarks": f"Purchase from {self.vendor}"
		})
		
		# 2. Debit Tax account (if tax exists)
		if self.tax_amount > 0:
			tax_account = org.default_tax_account if hasattr(org, 'default_tax_account') else None
			
			# Fallback: Find or create tax account
			if not tax_account:
				tax_account = frappe.db.get_value("IB Chart of Accounts", {"account_name": ["like", "%Tax%"]})
			
			if not tax_account:
				# Auto-create default tax account
				tax_doc = frappe.get_doc({
					"doctype": "IB Chart of Accounts",
					"account_name": "Input Tax - Organization",
					"account_type": "Asset",
					"root_type": "Asset",
					"is_group": 0
				})
				tax_doc.insert(ignore_permissions=True)
				frappe.db.commit()
				tax_account = tax_doc.name
			
			gl_entries.append({
				"account": tax_account,
				"debit": flt(self.tax_amount),
				"credit": 0,
				"remarks": f"Tax on purchase from {self.vendor}"
			})
		
		# 3. Debit/Credit Adjustment (if any)
		if self.adjustment and self.adjustment != 0:
			if self.adjustment > 0:
				# Positive adjustment increases expense
				gl_entries.append({
					"account": expense_account,
					"debit": flt(self.adjustment),
					"credit": 0,
					"remarks": f"Adjustment on purchase from {self.vendor}"
				})
			else:
				# Negative adjustment decreases expense
				gl_entries.append({
					"account": expense_account,
					"debit": 0,
					"credit": flt(abs(self.adjustment)),
					"remarks": f"Adjustment on purchase from {self.vendor}"
				})
		
		# 4. Credit Vendor account (grand total)
		vendor_account = frappe.db.get_value("IB Vendor", self.vendor, "default_payable_account")
		if not vendor_account:
			vendor_account = org.default_payable_account
		
		gl_entries.append({
			"account": vendor_account,
			"debit": 0,
			"credit": flt(self.grand_total),
			"remarks": f"Purchase from {self.vendor}",
			"party_type": "IB Vendor",
			"party": self.vendor
		})
		
		GLEngine.make_gl_entries(self, gl_entries)
	
	def update_purchase_order_status(self):
		"""Mark PO as Billed"""
		if self.purchase_order:
			frappe.db.set_value("IB Purchase Order", self.purchase_order, "status", "Billed")
