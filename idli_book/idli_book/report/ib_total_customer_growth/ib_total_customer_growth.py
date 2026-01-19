# Copyright (c) 2026, Praveen and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate, add_months, get_first_day, get_last_day, formatdate
from datetime import datetime
from dateutil.relativedelta import relativedelta


def execute(filters=None):
    """Main execution function for the IB Total Customer Growth report"""
    if not filters:
        filters = {}
    
    # Set default filter values
    filters = set_default_filters(filters)
    
    columns = get_columns(filters)
    data = get_data(filters)
    chart = get_chart_data(data, filters)
    report_summary = get_report_summary(data, filters)
    
    return columns, data, None, chart, report_summary


def set_default_filters(filters):
    """Set default filter values if not provided"""
    if not filters.get("from_date"):
        filters["from_date"] = add_months(getdate(), -12)
    if not filters.get("to_date"):
        filters["to_date"] = getdate()
    if not filters.get("period"):
        filters["period"] = "Monthly"
    return filters


def get_columns(filters):
    """Define report columns with proper formatting"""
    return [
        {
            "fieldname": "period",
            "label": _("Period"),
            "fieldtype": "Data",
            "width": 120
        },
        {
            "fieldname": "period_start",
            "label": _("Start Date"),
            "fieldtype": "Date",
            "width": 100,
            "hidden": 1
        },
        {
            "fieldname": "new_customers",
            "label": _("New Customers"),
            "fieldtype": "Int",
            "width": 130
        },
        {
            "fieldname": "total_customers",
            "label": _("Total Customers"),
            "fieldtype": "Int",
            "width": 130
        },
        {
            "fieldname": "growth_rate",
            "label": _("Growth Rate (%)"),
            "fieldtype": "Float",
            "precision": 2,
            "width": 130
        },
        {
            "fieldname": "active_customers",
            "label": _("Active Customers"),
            "fieldtype": "Int",
            "width": 130
        },
        {
            "fieldname": "retention_rate",
            "label": _("Retention Rate (%)"),
            "fieldtype": "Float",
            "precision": 2,
            "width": 130
        },
        {
            "fieldname": "churn_rate",
            "label": _("Churn Rate (%)"),
            "fieldtype": "Float",
            "precision": 2,
            "width": 120
        }
    ]


def get_data(filters):
    """Get customer growth data with comprehensive metrics"""
    from_date = getdate(filters.get("from_date"))
    to_date = getdate(filters.get("to_date"))
    period = filters.get("period", "Monthly")
    
    # Get all customers with creation date
    customers = frappe.db.sql("""
        SELECT 
            name,
            customer_name,
            DATE(creation) as creation_date
        FROM `tabIB Customer`
        WHERE DATE(creation) <= %(to_date)s
        ORDER BY creation
    """, {"to_date": to_date}, as_dict=1)
    
    # Get active customers (those with invoices in each period)
    invoices = frappe.db.sql("""
        SELECT 
            customer,
            invoice_date
        FROM `tabIB Sales Invoice`
        WHERE docstatus = 1
        AND invoice_date BETWEEN %(from_date)s AND %(to_date)s
    """, {"from_date": from_date, "to_date": to_date}, as_dict=1)
    
    # Build active customer map by period
    active_customer_map = build_active_customer_map(invoices, period)
    
    # Generate period data
    data = []
    periods = get_periods(from_date, to_date, period)
    previous_total = 0
    previous_active = 0
    
    for period_info in periods:
        period_key = period_info["key"]
        period_start = period_info["start"]
        period_end = period_info["end"]
        
        # Count new customers in this period
        new_in_period = len([
            c for c in customers 
            if c.creation_date and period_start <= getdate(c.creation_date) <= period_end
        ])
        
        # Count total customers up to period end
        total_up_to_period = len([
            c for c in customers 
            if c.creation_date and getdate(c.creation_date) <= period_end
        ])
        
        # Count active customers in period
        active_in_period = len(active_customer_map.get(period_key, set()))
        
        # Calculate growth rate
        if previous_total > 0:
            growth_rate = ((total_up_to_period - previous_total) / previous_total) * 100
        else:
            growth_rate = 100.0 if new_in_period > 0 else 0.0
        
        # Calculate retention rate (active customers / total customers)
        if total_up_to_period > 0:
            retention_rate = (active_in_period / total_up_to_period) * 100
        else:
            retention_rate = 0.0
        
        # Calculate churn rate (customers who became inactive)
        if previous_active > 0:
            # Customers who were active before but not now
            churned = max(0, previous_active - active_in_period + new_in_period)
            churn_rate = (churned / previous_active) * 100 if previous_active > 0 else 0.0
        else:
            churn_rate = 0.0
        
        data.append({
            "period": period_key,
            "period_start": period_start,
            "new_customers": new_in_period,
            "total_customers": total_up_to_period,
            "growth_rate": round(growth_rate, 2),
            "active_customers": active_in_period,
            "retention_rate": round(retention_rate, 2),
            "churn_rate": round(min(churn_rate, 100), 2)  # Cap at 100%
        })
        
        previous_total = total_up_to_period
        previous_active = active_in_period
    
    return data


def get_periods(from_date, to_date, period):
    """Generate list of periods between dates"""
    periods = []
    current_date = get_period_start(from_date, period)
    
    while current_date <= to_date:
        period_start = current_date
        period_end = get_period_end(current_date, period)
        
        # Don't exceed to_date
        if period_end > to_date:
            period_end = to_date
        
        periods.append({
            "key": get_period_key(current_date, period),
            "start": period_start,
            "end": period_end
        })
        
        current_date = get_next_period_start(current_date, period)
    
    return periods


def get_period_start(date, period):
    """Get the start of the period containing the given date"""
    if period == "Monthly":
        return get_first_day(date)
    elif period == "Quarterly":
        quarter_month = ((date.month - 1) // 3) * 3 + 1
        return date.replace(month=quarter_month, day=1)
    elif period == "Yearly":
        return date.replace(month=1, day=1)
    return get_first_day(date)


def get_period_end(date, period):
    """Get end date of period"""
    if period == "Monthly":
        return get_last_day(date)
    elif period == "Quarterly":
        quarter_end_month = ((date.month - 1) // 3 + 1) * 3
        return get_last_day(date.replace(month=quarter_end_month, day=1))
    elif period == "Yearly":
        return date.replace(month=12, day=31)
    return get_last_day(date)


def get_next_period_start(date, period):
    """Get start date of next period"""
    if period == "Monthly":
        return add_months(get_first_day(date), 1)
    elif period == "Quarterly":
        return add_months(get_first_day(date), 3)
    elif period == "Yearly":
        return date.replace(year=date.year + 1, month=1, day=1)
    return add_months(get_first_day(date), 1)


def get_period_key(date, period):
    """Get period key based on period type"""
    if period == "Monthly":
        return date.strftime("%b %Y")
    elif period == "Quarterly":
        quarter = (date.month - 1) // 3 + 1
        return f"Q{quarter} {date.year}"
    elif period == "Yearly":
        return str(date.year)
    return date.strftime("%b %Y")


def build_active_customer_map(invoices, period):
    """Build a map of active customers by period"""
    period_customers = {}
    
    for inv in invoices:
        if inv.invoice_date:
            period_key = get_period_key(getdate(inv.invoice_date), period)
            if period_key not in period_customers:
                period_customers[period_key] = set()
            period_customers[period_key].add(inv.customer)
    
    return period_customers


def get_chart_data(data, filters):
    """Generate production-ready chart configuration"""
    if not data:
        return None
    
    labels = [row["period"] for row in data]
    new_customers = [row["new_customers"] for row in data]
    total_customers = [row["total_customers"] for row in data]
    active_customers = [row["active_customers"] for row in data]
    
    # Calculate appropriate Y-axis scaling
    all_values = new_customers + total_customers + active_customers
    max_value = max(all_values) if all_values else 0
    
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
        "colors": ["#3b82f6", "#8b5cf6", "#10b981"],  # Blue, Purple, Green
        "axisOptions": {
            "xIsSeries": 1,
            "shortenYAxisNumbers": 0,
            "xAxisMode": "tick"
        },
        "barOptions": {
            "stacked": 0,
            "spaceRatio": 0.3
        },
        "lineOptions": {
            "regionFill": 1,
            "hideDots": 0,
            "dotSize": 5,
            "heatline": 0,
            "spline": 1
        },
        "tooltipOptions": {
            "formatTooltipX": "d => d",
            "formatTooltipY": "d => d + ' customers'"
        },
        "height": 350,
        "animate": 1,
        "truncateLegends": 0,
        "valuesOverPoints": 1
    }
    
    return chart


def get_report_summary(data, filters):
    """Generate report summary cards"""
    if not data:
        return []
    
    # Get totals
    total_new = sum(row["new_customers"] for row in data)
    current_total = data[-1]["total_customers"] if data else 0
    current_active = data[-1]["active_customers"] if data else 0
    
    # Calculate overall growth
    first_total = data[0]["total_customers"] if data else 0
    if first_total > 0:
        overall_growth = ((current_total - first_total) / first_total) * 100
    else:
        overall_growth = 100.0 if current_total > 0 else 0.0
    
    # Average retention rate
    avg_retention = sum(row["retention_rate"] for row in data) / len(data) if data else 0
    
    return [
        {
            "value": total_new,
            "indicator": "Green" if total_new > 0 else "Grey",
            "label": _("New Customers Added"),
            "datatype": "Int"
        },
        {
            "value": current_total,
            "indicator": "Blue",
            "label": _("Total Customers"),
            "datatype": "Int"
        },
        {
            "value": current_active,
            "indicator": "Green" if current_active > 0 else "Grey",
            "label": _("Currently Active"),
            "datatype": "Int"
        },
        {
            "value": round(overall_growth, 2),
            "indicator": "Green" if overall_growth > 0 else "Red",
            "label": _("Overall Growth (%)"),
            "datatype": "Percent"
        },
        {
            "value": round(avg_retention, 2),
            "indicator": "Green" if avg_retention >= 50 else "Orange",
            "label": _("Avg Retention Rate (%)"),
            "datatype": "Percent"
        }
    ]
