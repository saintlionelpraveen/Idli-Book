
import frappe
from frappe.model.document import Document
from frappe.utils import flt

class IBJournalEntry(Document):
	def validate(self):
		self.calculate_totals()
		
		# Validation: Debit must equal Credit
		if self.total_debit != self.total_credit:
			frappe.throw(f"Total Debit ({self.total_debit}) must equal Total Credit ({self.total_credit})")
			
		if self.total_debit == 0:
			frappe.throw("Journal Entry cannot be empty")

	def calculate_totals(self):
		total_debit = 0.0
		total_credit = 0.0
		
		for row in self.entries:
			row.debit = flt(row.debit)
			row.credit = flt(row.credit)
			
			total_debit += row.debit
			total_credit += row.credit
			
		self.total_debit = total_debit
		self.total_credit = total_credit

	def on_submit(self):
		# Additional validation
		self.validate()
		self.make_gl_entries()

	def on_cancel(self):
		from idli_book.idli_book.gl_engine import GLEngine
		GLEngine.delete_gl_entries(self)

	def make_gl_entries(self):
		from idli_book.idli_book.gl_engine import GLEngine
		gl_entries = []
		
		for row in self.entries:
			# Check for conflicting entries
			if row.debit > 0 and row.credit > 0:
				frappe.throw(f"Row {row.idx}: Cannot have both Debit and Credit. Use separate rows.")
				
			gl_entries.append({
				"account": row.account,
				"party_type": row.party_type,
				"party": row.party,
				"debit": row.debit,
				"credit": row.credit,
				"remarks": row.description or self.user_remark or f"JV {self.name}"
			})
			
		GLEngine.make_gl_entries(self, gl_entries)
