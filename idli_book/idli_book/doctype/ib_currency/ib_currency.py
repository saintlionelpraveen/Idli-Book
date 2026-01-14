# Copyright (c) 2026, Praveen and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class IBCurrency(Document):
	def validate(self):
		"""Validate currency data"""
		# Ensure currency code is uppercase
		if self.currency_code:
			self.currency_code = self.currency_code.upper()
		
		# Validate currency code format (3 letters)
		if self.currency_code and len(self.currency_code) != 3:
			frappe.throw("Currency Code must be exactly 3 characters (e.g., INR, USD)")
