// Copyright (c) 2026, Praveen and contributors
// For license information, please see license.txt

frappe.query_reports["IB Total Customer Growth"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -12),
            "reqd": 1,
            "width": "80px"
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1,
            "width": "80px"
        },
        {
            "fieldname": "period",
            "label": __("Period"),
            "fieldtype": "Select",
            "options": "Monthly\nQuarterly\nYearly",
            "default": "Monthly",
            "width": "80px"
        }
    ],

    "formatter": function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        if (!data) return value;

        // Color code the growth rate
        if (column.fieldname === "growth_rate") {
            let rate = parseFloat(data.growth_rate || 0);
            if (rate > 0) {
                value = `<span style="color: #10b981; font-weight: 600;">▲ ${rate.toFixed(2)}%</span>`;
            } else if (rate < 0) {
                value = `<span style="color: #ef4444; font-weight: 600;">▼ ${Math.abs(rate).toFixed(2)}%</span>`;
            } else {
                value = `<span style="color: #6b7280;">0.00%</span>`;
            }
        }

        // Color code retention rate
        if (column.fieldname === "retention_rate") {
            let rate = parseFloat(data.retention_rate || 0);
            if (rate >= 70) {
                value = `<span style="color: #10b981; font-weight: 600;">${rate.toFixed(2)}%</span>`;
            } else if (rate >= 40) {
                value = `<span style="color: #f59e0b; font-weight: 600;">${rate.toFixed(2)}%</span>`;
            } else {
                value = `<span style="color: #ef4444; font-weight: 600;">${rate.toFixed(2)}%</span>`;
            }
        }

        // Color code churn rate (lower is better)
        if (column.fieldname === "churn_rate") {
            let rate = parseFloat(data.churn_rate || 0);
            if (rate <= 10) {
                value = `<span style="color: #10b981; font-weight: 600;">${rate.toFixed(2)}%</span>`;
            } else if (rate <= 30) {
                value = `<span style="color: #f59e0b; font-weight: 600;">${rate.toFixed(2)}%</span>`;
            } else {
                value = `<span style="color: #ef4444; font-weight: 600;">${rate.toFixed(2)}%</span>`;
            }
        }

        // Highlight new customers
        if (column.fieldname === "new_customers" && data.new_customers > 0) {
            value = `<span style="color: #3b82f6; font-weight: 600;">+${data.new_customers}</span>`;
        }

        // Highlight total customers
        if (column.fieldname === "total_customers") {
            value = `<span style="font-weight: 600;">${data.total_customers}</span>`;
        }

        // Highlight active customers with color based on ratio
        if (column.fieldname === "active_customers" && data.total_customers > 0) {
            let ratio = data.active_customers / data.total_customers;
            let color = ratio >= 0.5 ? "#10b981" : ratio >= 0.25 ? "#f59e0b" : "#ef4444";
            value = `<span style="color: ${color}; font-weight: 600;">${data.active_customers}</span>`;
        }

        return value;
    },

    "after_datatable_render": function (datatable) {
        // Add custom styling to the report
        const style = document.createElement('style');
        style.textContent = `
            .dt-row .dt-cell {
                padding: 10px 12px;
            }
            .dt-row:hover {
                background-color: rgba(59, 130, 246, 0.05);
            }
        `;
        document.head.appendChild(style);
    }
};
