
import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate, add_days


class IBSalesInvoice(Document):
	def validate(self):
		self.set_dates()
		self.calculate_totals()
		self.auto_fetch_address_details()
		
		# Clear payment references if this is an amended document
		if self.amended_from and self.docstatus == 0:
			self.clear_amended_references()
	
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
					row_net = row.amount / (1 + (row.tax_rate / 100))
					row_tax = row.amount - row_net
			else:
				if row.tax_rate:
					row_tax = row.amount * (row.tax_rate / 100)
			
			subtotal += row_net
			total_tax += row_tax
			
		self.subtotal = flt(subtotal)
		
		# Apply Discount
		self.discount_amount = flt(self.discount_amount)
		if self.discount_type == "Percentage":
			if self.discount_percentage:
				self.discount_amount = self.subtotal * (self.discount_percentage / 100)
			else:
				self.discount_amount = 0
		elif self.discount_type == "None":
			self.discount_amount = 0
			
		grand_total = self.subtotal - self.discount_amount + total_tax + flt(self.adjustment)
		self.tax_amount = total_tax
		self.grand_total = flt(grand_total)
		
		if self.status == "Draft":
			self.outstanding_amount = self.grand_total

	def auto_fetch_address_details(self):
		if self.customer:
			if not self.shipping_address:
				addr = frappe.db.get_value("IB Customer", self.customer, "billing_address")
				if addr: self.shipping_address = addr
			
			if not self.place_of_supply:
				state = frappe.db.get_value("IB Customer", self.customer, "state")
				if state: self.place_of_supply = state

	def on_submit(self):
		if self.outstanding_amount < 0: 
			frappe.throw("Outstanding amount cannot be negative")
			
		self.status = "Awaiting Payment"
		if not self.paid_amount:
			self.paid_amount = 0
			self.outstanding_amount = self.grand_total

		self.posting_date = self.invoice_date
		
		try:
			self.make_gl_entries()
		except Exception as e:
			frappe.log_error("GL Entry Creation Failed", f"Invoice: {self.name}\nError: {str(e)}")
			frappe.throw(f"Failed to create accounting entries: {str(e)}")
		
		self.update_stock(-1)
		self.send_invoice_email()
	
	def clear_amended_references(self):
		try:
			refs = frappe.get_all("IB Payment Reference", 
				filters={"reference_name": self.amended_from},
				fields=["name", "parent"])
			
			for ref in refs:
				frappe.db.delete("IB Payment Reference", {"name": ref.name})
				frappe.msgprint(f"Cleared payment reference from {ref.parent}")
		except Exception as e:
			frappe.log_error("Amendment Reference Cleanup", str(e))

	def send_invoice_email(self):
		customer_email = frappe.db.get_value("IB Customer", self.customer, "email")
		
		if customer_email:
			from frappe.utils import validate_email_address
			try:
				validate_email_address(customer_email, throw=True)
			except:
				frappe.log_error("Invalid Email", f"Customer: {self.customer}, Email: {customer_email}")
				frappe.msgprint(f"Warning: Setup valid email for customer {self.customer} to send invoice.")
				return

		if customer_email:
			org_name = frappe.db.get_single_value('IB Organization', 'organization_name') or "Our Company"
			subject = f"Invoice #{self.name} from {org_name}"
			
			message = f"""
			<div style="font-family: Arial, sans-serif; padding: 20px;">
				<h3>Invoice #{self.name}</h3>
				<p>Hello {self.customer},</p>
				<p>Please find attached invoice for <b>{frappe.format(self.grand_total, {'fieldtype': 'Currency'})}</b>.</p>
				<p><b>Status:</b> {self.status}</p>
				<p><b>Due Date:</b> {frappe.utils.formatdate(self.due_date)}</p>
			"""
			
			settings = frappe.get_single("IB Payment Settings")
			
			if getattr(settings, 'enable_upi_qr', False) and self.outstanding_amount > 0:
				pay_url = frappe.utils.get_url(f"/invoice_payment?invoice={self.name}")
				message += f"""
				<div style="margin: 20px 0; text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px;">
					<a href="{pay_url}" style="background-color: white; color: #667eea; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block; font-size: 16px;">
						📱 Pay Now via UPI: {frappe.format(self.outstanding_amount, {'fieldtype': 'Currency'})}
					</a>
				</div>
				"""
			elif settings.enable_payment_gateway and self.outstanding_amount > 0:
				pay_url = frappe.utils.get_url(f"/pay?invoice={self.name}")
				message += f"""
				<div style="margin: 20px 0;">
					<a href="{pay_url}" style="background-color: #5b45ff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">
						Pay Now: {frappe.format(self.outstanding_amount, {'fieldtype': 'Currency'})}
					</a>
				</div>
				"""

			message += f"""
				<br>
				<p>Best Regards,<br>{org_name}</p>
			</div>
			"""
			try:
				frappe.sendmail(
					recipients=customer_email,
					subject=subject,
					message=message,
					reference_doctype=self.doctype,
					reference_name=self.name,
					attachments=[frappe.attach_print(self.doctype, self.name, print_format="Standard")]
				)
				self.db_set('email_delivery_status', 'Queued')
			except:
				self.db_set('email_delivery_status', 'Error')

	def make_gl_entries(self):
		from idli_book.idli_book.gl_engine import GLEngine
		
		gl_entries = []
		org = frappe.get_doc("IB Organization", "IB Organization")
		
		# 1. Customer (Dr) - Use customer's linked account or org default
		customer_acct = frappe.db.get_value("IB Customer", self.customer, "default_receivable_account")
		if not customer_acct:
			customer_acct = org.default_receivable_account
			
		gl_entries.append({
			"account": customer_acct,
			"party_type": "IB Customer",
			"party": self.customer,
			"debit": self.grand_total,
			"credit": 0,
			"remarks": "Invoice " + self.name
		})
		
		# 2. Income (Cr)
		default_income = org.default_income_account
		
		for row in self.items:
			item_doc = frappe.get_doc("IB Item", row.item_code)
			income_acct = getattr(item_doc, 'default_income_account', None) or default_income
			
			gl_entries.append({
				"account": income_acct,
				"debit": 0,
				"credit": row.amount or 0,
				"remarks": f"Income - {row.item_code}"
			})
		
		# 3. Tax (Cr)
		if self.tax_amount > 0:
			tax_acct = org.gst_output_account
			gl_entries.append({
				"account": tax_acct,
				"debit": 0,
				"credit": self.tax_amount,
				"remarks": f"Tax on {self.name}"
			})

		# 4. Discount (Dr)
		if self.discount_amount > 0:
			discount_acct = org.discount_account
			gl_entries.append({
				"account": discount_acct,
				"debit": self.discount_amount,
				"credit": 0,
				"remarks": f"Discount on {self.name}"
			})

		# 5. Adjustment
		if self.adjustment:
			round_off_acct = org.round_off_account
			entry = {
				"account": round_off_acct,
				"remarks": "Adjustment/Round Off"
			}
			if self.adjustment > 0:
				entry.update({"debit": 0, "credit": self.adjustment})
			else:
				entry.update({"debit": abs(self.adjustment), "credit": 0})
			gl_entries.append(entry)

		GLEngine.make_gl_entries(self, gl_entries)

	def update_stock(self, factor):
		org_email = frappe.session.user

		for row in self.items:
			item_data = frappe.db.get_value("IB Item", row.item_code, ["track_inventory", "stock_quantity", "reorder_level", "item_name"], as_dict=True)
			
			if item_data and item_data.track_inventory:
				current_qty = flt(item_data.stock_quantity)
				new_qty = current_qty + (flt(row.quantity) * factor)
				
				frappe.db.set_value("IB Item", row.item_code, "stock_quantity", new_qty)
				
				if item_data.reorder_level and new_qty < flt(item_data.reorder_level):
					self.send_reorder_alert(row.item_code, item_data.item_name, new_qty, item_data.reorder_level, org_email)

	def send_reorder_alert(self, item_code, item_name, current_qty, reorder_level, user_email):
		admin_users = frappe.get_all("Has Role", 
			filters={"role": "System Manager", "parenttype": "User"},
			fields=["parent"]
		)
		
		recipient_emails = [user.parent for user in admin_users]
		if not recipient_emails:
			recipient_emails = [user_email]
		
		org_name = frappe.db.get_single_value('IB Organization', 'organization_name') or "Your Organization"
		subject = f"⚠️ Low Stock Alert: {item_name}"
		
		message = f"""
		<div style="font-family: Arial, sans-serif; padding: 20px; max-width: 600px;">
			<div style="background-color: #fff3cd; border-left: 5px solid #ffc107; padding: 15px; margin-bottom: 20px;">
				<h2 style="color: #dc3545; margin: 0 0 10px 0;">⚠️ Low Stock Alert</h2>
				<p style="color: #856404; margin: 0;">Immediate attention required for inventory replenishment</p>
			</div>
			
			<p>The stock for <strong>{item_name}</strong> ({item_code}) has dropped to <strong>{current_qty}</strong>, below reorder level of <strong>{reorder_level}</strong>.</p>
			
			<p style="color: #6c757d; font-size: 12px; margin-top: 30px;">
				Best Regards,<br>
				<strong>{org_name}</strong>
			</p>
		</div>
		"""
		try:
			frappe.sendmail(recipients=recipient_emails, subject=subject, message=message)
		except Exception as e:
			frappe.log_error("Stock Alert Failed", str(e))
