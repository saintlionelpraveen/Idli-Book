frappe.listview_settings['IB Payment'] = {
    add_fields: ["payment_type", "docstatus"],

    get_indicator: function (doc) {
        if (doc.docstatus === 2) {
            return [__("Cancelled"), "red", "docstatus,=,2"];
        }
        if (doc.docstatus === 1) {
            return [__("Submitted"), "blue", "docstatus,=,1"];
        }
        return [__("Draft"), "grey", "docstatus,=,0"];
    },

    formatters: {
        payment_type: function (val, doc) {
            if (val === "Receive") {
                // Green Badge for Sales
                return `<span class="indicator-pill green" style="background-color: #d1fae5; color: #065f46; font-weight: bold; padding: 4px 8px;">Sales</span>`;
            } else if (val === "Pay") {
                // Red Badge for Purchase
                return `<span class="indicator-pill red" style="background-color: #fee2e2; color: #991b1b; font-weight: bold; padding: 4px 8px;">Purchase</span>`;
            }
            return val;
        }
    }
};
