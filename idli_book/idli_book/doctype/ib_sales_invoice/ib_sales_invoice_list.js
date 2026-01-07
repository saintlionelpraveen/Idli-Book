frappe.listview_settings['IB Sales Invoice'] = {
    add_fields: ["email_delivery_status", "status"],
    get_indicator: function (doc) {
        if (doc.email_delivery_status === "Error") {
            return [__("Email Error"), "red", "email_delivery_status,=,Error"];
        }
        const status_colors = {
            "Draft": "grey",
            "Unpaid": "red",
            "Partly Paid": "orange",
            "Paid": "green",
            "Overdue": "red",
            "Cancelled": "red"
        };
        return [__(doc.status), status_colors[doc.status] || "grey", "status,=," + doc.status];
    },
    formatters: {
        email_delivery_status: function (val) {
            const colors = {
                "Not Sent": "grey",
                "Queued": "orange",
                "Sent": "green",
                "Error": "red"
            };
            const color = colors[val] || "grey";
            return `<span class="indicator-pill ${color}">${val}</span>`;
        }
    }
};
