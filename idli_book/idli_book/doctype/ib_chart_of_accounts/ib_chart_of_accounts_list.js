frappe.listview_settings['IB Chart of Accounts'] = {
    get_indicator: function (doc) {
        // Color indicators based on owner type
        if (doc.owner_type === "Organization") {
            return [__("Organization"), "red", "owner_type,=,Organization"];
        } else if (doc.owner_type === "Customer") {
            return [__("Customer"), "green", "owner_type,=,Customer"];
        } else if (doc.owner_type === "Vendor") {
            return [__("Vendor"), "yellow", "owner_type,=,Vendor"];
        }
        return [__("General"), "blue", "owner_type,=,"];
    },

    formatters: {
        account_name: function (value, field, doc) {
            // Add colored badge before account name
            let badge = '';
            if (doc.owner_type === "Organization") {
                badge = '<span class="indicator-pill red" style="margin-right: 5px;">ORG</span>';
            } else if (doc.owner_type === "Customer") {
                badge = '<span class="indicator-pill green" style="margin-right: 5px;">CUST</span>';
            } else if (doc.owner_type === "Vendor") {
                badge = '<span class="indicator-pill orange" style="margin-right: 5px;">VEND</span>';
            }
            return badge + value;
        }
    }
};
