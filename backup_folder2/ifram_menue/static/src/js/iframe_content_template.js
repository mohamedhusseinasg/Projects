/** @odoo-module */
import { ControlPanel } from "@web/search/control_panel/control_panel";
import { patch } from "@web/core/utils/patch";
import { onMounted } from "@odoo/owl";

patch(ControlPanel.prototype, {
    setup() {
        super.setup();

        onMounted(async () => {
            const searchModel = this.env.searchModel;
            if (searchModel && searchModel.resModel === 'iframe.iframe') {
                const currentViewId = String(this.env.config.viewId); // Convert to string
                console.log("Current View ID:", currentViewId); // Log current view ID for debugging
                const modelName = searchModel.resModel;
                console.log("Model Name:", modelName); // Log model name
                const orm = this.env.services.orm;
                try {
                    const viewData = await orm.call(
                        'ir.ui.view', 'read', [[parseInt(currentViewId)], ['name']]
                    );
                    if (viewData && viewData.length > 0) {
                        const viewName = viewData[0].name;
                        console.log("Form View Name:", viewName); // Log form view name

                        if (viewName !== 'Iframe View' && viewName !== 'Iframe View tree') {
                            console.log("Hiding control panel for view:", viewName); // Log hiding action
                            this.root.el.style.setProperty("display", "none", "important");
                        } else {
                            console.log("Keeping control panel visible for view:", viewName); // Log keeping visible action
                        }
                    } else {
                        console.warn("View data not found for view ID:", viewName);
                    }
                } catch (error) {
                    console.error("Error fetching view data:", error);
                }
            } else {
                console.warn("Search model or resModel not found:", searchModel); // Log if search model or resModel is not found
            }
        });
    },
});


///** @odoo-module */
//import { ControlPanel } from "@web/search/control_panel/control_panel";
//import { patch } from "@web/core/utils/patch";
//import { useRef, onPatched, onMounted, useState } from "@odoo/owl";
//patch(ControlPanel.prototype,{
//    setup() {
//        super.setup();
//        onMounted(() => {
//            if (this.env.searchModel && this.env.searchModel.resModel == 'iframe.iframe') {
//                this.root.el.style.setProperty("display", "none", "important");
//            }
//        });
//    },
//});
//


