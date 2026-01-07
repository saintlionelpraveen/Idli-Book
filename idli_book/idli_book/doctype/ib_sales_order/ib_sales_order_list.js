frappe.listview_settings['IB Sales Order'] = {
    add_fields: ["email_delivery_status", "status"],
    get_indicator: function (doc) {
        if (doc.email_delivery_status === "Error") {
            return [__("Email Error"), "red", "email_delivery_status,=,Error"];
        }
        const status_colors = {
            "Draft": "grey",
            "To Bill": "orange",
            "To Deliver": "orange",
            "Completed": "green",
            "Cancelled": "red",
            "Overdue": "red"
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
