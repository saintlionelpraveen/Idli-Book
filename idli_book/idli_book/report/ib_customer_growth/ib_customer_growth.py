# Copyright (c) 2026, Praveen and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate, add_months, add_to_date, formatdate
from datetime import datetime
from dateutil.relativedelta import relativedelta

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	chart = get_chart_data(data, filters)
	
	return columns, data, None, chart

def get_columns(filters):
	"""Define report columns"""
	return [
		{
			"fieldname": "period",
			"label": _("Period"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "new_customers",
			"label": _("New Customers"),
			"fieldtype": "Int",
			"width": 120
		},
		{
			"fieldname": "total_customers",
			"label": _("Total Customers"),
			"fieldtype": "Int",
			"width": 120
		},
		{
			"fieldname": "growth_rate",
			"label": _("Growth Rate (%)"),
			"fieldtype": "Percent",
			"width": 130
		},
		{
			"fieldname": "active_customers",
			"label": _("Active Customers"),
			"fieldtype": "Int",
			"width": 130
		}
	]

def get_data(filters):
	"""Get customer growth data"""
	from_date = getdate(filters.get("from_date"))
	to_date = getdate(filters.get("to_date"))
	period = filters.get("period", "Monthly")
	
	# Get all customers with creation date
	customers = frappe.db.sql("""
		SELECT 
			name,
			customer_name,
			creation,
			modified
		FROM `tabIB Customer`
		WHERE creation <= %(to_date)s
		ORDER BY creation
	""", {"to_date": to_date}, as_dict=1)
	
	# Get customers with invoices (active customers)
	active_customer_map = get_active_customers(from_date, to_date)
	
	# Group by period
	period_data = {}
	current_date = from_date
	previous_total = 0
	
	while current_date <= to_date:
		period_key = get_period_key(current_date, period)
		period_end = get_period_end(current_date, period)
		
		# Count new customers in this period
		new_in_period = len([c for c in customers if getdate(c.creation) >= current_date and getdate(c.creation) <= period_end])
		
		# Count total customers up to period end
		total_up_to_period = len([c for c in customers if getdate(c.creation) <= period_end])
		
		# Count active customers in period
		active_in_period = sum(1 for c in customers if c.name in active_customer_map.get(period_key, []))
		
		# Calculate growth rate
		if previous_total > 0:
			growth_rate = ((total_up_to_period - previous_total) / previous_total) * 100
		else:
			growth_rate = 100.0 if total_up_to_period > 0 else 0.0
		
		period_data[period_key] = {
			"period": period_key,
			"new_customers": new_in_period,
			"total_customers": total_up_to_period,
			"growth_rate": f"{growth_rate:.2f}%",
			"active_customers": active_in_period
		}
		
		previous_total = total_up_to_period
		current_date = get_next_period_start(current_date, period)
	
	# Convert to list and sort
	data = list(period_data.values())
	data.sort(key=lambda x: x["period"])
	
	return data

def get_active_customers(from_date, to_date):
	"""Get customers who made purchases in each period"""
	invoices = frappe.db.sql("""
		SELECT 
			customer,
			invoice_date
		FROM `tabIB Sales Invoice`
		WHERE docstatus = 1
		AND invoice_date BETWEEN %(from_date)s AND %(to_date)s
	""", {"from_date": from_date, "to_date": to_date}, as_dict=1)
	
	# Group by period
	period_customers = {}
	for inv in invoices:
		period_key = formatdate(inv.invoice_date, "MMM yyyy")
		if period_key not in period_customers:
			period_customers[period_key] = set()
		period_customers[period_key].add(inv.customer)
	
	return period_customers

def get_period_key(date, period):
	"""Get period key based on period type"""
	if period == "Monthly":
		return formatdate(date, "MMM yyyy")
	elif period == "Quarterly":
		quarter = (date.month - 1) // 3 + 1
		return f"Q{quarter} {date.year}"
	elif period == "Yearly":
		return str(date.year)
	return formatdate(date, "MMM yyyy")

def get_period_end(date, period):
	"""Get end date of period"""
	if period == "Monthly":
		return add_to_date(date, months=1, days=-1)
	elif period == "Quarterly":
		return add_to_date(date, months=3, days=-1)
	elif period == "Yearly":
		return add_to_date(date, years=1, days=-1)
	return date

def get_next_period_start(date, period):
	"""Get start date of next period"""
	if period == "Monthly":
		return add_months(date, 1)
	elif period == "Quarterly":
		return add_months(date, 3)
	elif period == "Yearly":
		return add_to_date(date, years=1)
	return add_months(date, 1)

def get_chart_data(data, filters):
	"""Generate chart configuration with proper formatting for production use"""
	if not data:
		return None
	
	# Sort data by date to ensure proper chronological order
	sorted_data = sorted(data, key=lambda x: parse_period_to_date(x["period"], filters.get("period", "Monthly")))
	
	labels = [row["period"] for row in sorted_data]
	new_customers = [row["new_customers"] for row in sorted_data]
	total_customers = [row["total_customers"] for row in sorted_data]
	active_customers = [row["active_customers"] for row in sorted_data]
	
	# Calculate dynamic Y-axis max to avoid duplicate tick labels
	max_value = max(max(new_customers) if new_customers else 0,
					max(total_customers) if total_customers else 0,
					max(active_customers) if active_customers else 0)
	
	# Ensure at least 5 for better axis display
	y_max = max(max_value + 2, 5)
	
	chart = {
		"data": {
			"labels": labels,
			"datasets": [
				{
					"name": _("New Customers"),
					"values": new_customers,
					"chartType": "bar"
				},
				{
					"name": _("Total Customers"),
					"values": total_customers,
					"chartType": "line"
				},
				{
					"name": _("Active Customers"),
					"values": active_customers,
					"chartType": "line"
				}
			]
		},
		"type": "axis-mixed",
		"colors": ["#4299e1", "#9f7aea", "#48bb78"],
		"axisOptions": {
			"xIsSeries": 1,
			"shortenYAxisNumbers": 0,
			"xAxisMode": "tick"
		},
		"barOptions": {
			"stacked": 0,
			"spaceRatio": 0.4
		},
		"lineOptions": {
			"regionFill": 1,
			"hideDots": 0,
			"dotSize": 4,
			"heatline": 0
		},
		"tooltipOptions": {
			"formatTooltipX": "d => d"
		},
		"height": 320,
		"animate": 1,
		"truncateLegends": 0
	}
	
	return chart


def parse_period_to_date(period_str, period_type):
	"""Parse period string back to date for proper sorting"""
	from datetime import datetime
	
	try:
		if period_type == "Monthly":
			# Format: "Jan 2025"
			return datetime.strptime(period_str, "%b %Y")
		elif period_type == "Quarterly":
			# Format: "Q1 2025"
			quarter = int(period_str[1])
			year = int(period_str.split()[1])
			month = (quarter - 1) * 3 + 1
			return datetime(year, month, 1)
		elif period_type == "Yearly":
			# Format: "2025"
			return datetime(int(period_str), 1, 1)
	except (ValueError, IndexError):
		pass
	
	# Fallback - return current date
	return datetime.now()

