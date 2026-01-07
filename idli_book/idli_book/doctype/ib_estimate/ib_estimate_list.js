frappe.listview_settings['IB Estimate'] = {
    add_fields: ["email_delivery_status", "status"],
    get_indicator: function (doc) {
        // Prioritize Email Status if it's relevant (e.g. Error or Sent)
        // Or keep standard status but show email status as a badge?
        // User asked to "enhance visual". Colored dot is good.

        // Standard Frappe only supports ONE indicator dot per row on the left.
        // We probably want to keep the Main Status (Open, Submitted) as the main dot.
        // But the user said "if the mail is not sent the status colour is red".

        // Let's create a logic that prioritizes the 'health' of the doc.

        if (doc.email_delivery_status === "Error") {
            return [__("Email Error"), "red", "email_delivery_status,=,Error"];
        }

        // If everything is normal, return standard statuses
        const status_colors = {
            "Draft": "grey",
            "Submitted": "blue",
            "Accepted": "green",
            "Halted": "gray",
            "Ordered": "green",
            "Cancelled": "red"
        };

        return [__(doc.status), status_colors[doc.status] || "grey", "status,=," + doc.status];
    },

    // Check if we can format the email delivery status column itself
    formatters: {
        email_delivery_status: function (val) {
            const colors = {
                "Not Sent": "grey",
                "Queued": "orange",
                "Sent": "green",
                "Error": "red"
            };
            const color = colors[val] || "grey";
            // Return a pill/badge
            return `<span class="indicator-pill ${color}">${val}</span>`;
        }
    }
};
