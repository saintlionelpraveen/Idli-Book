
import frappe
from frappe.utils import flt

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		{
			"fieldname": "account",
			"label": "Account",
			"fieldtype": "Link",
			"options": "IB Chart of Accounts",
			"width": 300
		},
		{
			"fieldname": "opening_debit",
			"label": "Opening Debit",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "opening_credit",
			"label": "Opening Credit",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "debit",
			"label": "Debit",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "credit",
			"label": "Credit",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "closing_debit",
			"label": "Closing Debit",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "closing_credit",
			"label": "Closing Credit",
			"fieldtype": "Currency",
			"width": 120
		}
	]

def get_data(filters):
	data = []
	accounts = frappe.get_all("IB Chart of Accounts", fields=["name", "account_name", "parent_account", "is_group"])
	
	# Fetch GL Entries
	gl_entries = frappe.db.sql("""
		SELECT account, debit, credit, posting_date
		FROM `tabIB GL Entry`
		ORDER BY posting_date
	""", as_dict=1)
	
	# Process Data
	# This is a simple implementation. For production, efficient SQL aggregations are better.
	
	acc_map = {acc.name: {"opening": 0.0, "debit": 0.0, "credit": 0.0} for acc in accounts}
	
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	
	for gle in gl_entries:
		if gle.account not in acc_map: continue
		
		# Opening Balance (Before From Date)
		if str(gle.posting_date) < str(from_date):
			acc_map[gle.account]["opening"] += (flt(gle.debit) - flt(gle.credit))
			
		# Period Transaction (Within Dates)
		elif str(gle.posting_date) <= str(to_date):
			acc_map[gle.account]["debit"] += flt(gle.debit)
			acc_map[gle.account]["credit"] += flt(gle.credit)
			
	# Construct Result
	for acc in accounts:
		# Skip groups for now or calculate manually? 
		# Simple Trial Balance often shows leaf accounts.
		# Let's show all for flat view, hierarchy is complex for JS Tree.
		# We'll stick to simple list.
		
		vals = acc_map.get(acc.name, {})
		opening = vals.get("opening", 0.0)
		debit = vals.get("debit", 0.0)
		credit = vals.get("credit", 0.0)
		
		closing = opening + debit - credit
		
		# Determine Dr/Cr placement
		res = {
			"account": acc.name,
			"opening_debit": opening if opening > 0 else 0,
			"opening_credit": abs(opening) if opening < 0 else 0,
			"debit": debit,
			"credit": credit,
			"closing_debit": closing if closing > 0 else 0,
			"closing_credit": abs(closing) if closing < 0 else 0
		}
		
		# Filter out zero rows? Maybe keep them if they had movement.
		if debit != 0 or credit != 0 or opening != 0:
			data.append(res)
			
	return data
