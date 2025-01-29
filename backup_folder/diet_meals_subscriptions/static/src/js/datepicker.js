/** @odoo-module **/

import { Component } from '@odoo/owl';
import { useBus, useExternalListener } from '@web/core/utils/hooks';
import { DatePicker } from '@web/core/datepicker/datepicker';
import { formatDateTime, formatDate } from '@web/core/utils/formatters';
import { registry } from '@web/core/registry';

const { onMounted, useState } = owl;

export class CustomDatePicker extends Component {
    setup() {
        this.state = useState({
            isOpen: false,
            options: this.getOptions(),
        });

        // Use external listener to track the 'open' state
        useExternalListener(window, 'hide.datetimepicker', () => {
            this.state.isOpen = false;
        });
        useExternalListener(window, 'show.datetimepicker', () => {
            this.state.isOpen = true;
        });
    }

    getOptions() {
        let options = {
            locale: moment.locale(),
            format: this.props.type_of_date === 'datetime' ? formatDateTime : formatDate,
            minDate: moment({ y: 1000 }),
            maxDate: moment({ y: 9999, M: 11, d: 31 }),
            useCurrent: false,
            icons: {
                time: 'fa fa-clock-o',
                date: 'fa fa-calendar',
                up: 'fa fa-chevron-up',
                down: 'fa fa-chevron-down',
                previous: 'fa fa-chevron-left',
                next: 'fa fa-chevron-right',
                today: 'fa fa-calendar-check-o',
                clear: 'fa fa-trash',
                close: 'fa fa-check primary',
            },
            calendarWeeks: true,
            buttons: {
                showToday: false,
                showClear: false,
                showClose: false,
            },
            widgetParent: 'body',
            keyBinds: null,
        };

        // Include minDate from parent.recordData if available
        if (this.props.parent && this.props.parent.recordData.minDate) {
            options.minDate = this.props.parent.recordData.minDate;
        }

        return options;
    }

    onDateChange(ev) {
        // Handle date change event
    }
}

// Register the component
registry.category('fields').add('custom_datepicker', CustomDatePicker);

// odoo.define('diet_meals_subscriptions.datepicker', function (require) {
//     "use strict";
//     var datepicker = require('web.datepicker');

//     var core = require('web.core');
//     var field_utils = require('web.field_utils');
//     var time = require('web.time');
//     var Widget = require('web.Widget');

//     var _t = core._t;


//     datepicker.DateWidget.include({
//         init: function (parent, options) {
//             this._super.apply(this, arguments);
//             if ('minDate' in parent.recordData && !!parent.recordData.minDate)
//                 options.minDate = parent.recordData.minDate
//             // if ('maxDate' in parent.recordData && !!parent.recordData.maxDate)
//             //     options.maxDate = parent.recordData.maxDate
//             this.name = parent.name;
//             this.options = _.extend({
//                 locale: moment.locale(),
//                 format: this.type_of_date === 'datetime' ? time.getLangDatetimeFormat() : time.getLangDateFormat(),
//                 minDate: moment({ y: 1000 }),
//                 maxDate: moment({ y: 9999, M: 11, d: 31 }),
//                 useCurrent: false,
//                 icons: {
//                     time: 'fa fa-clock-o',
//                     date: 'fa fa-calendar',
//                     up: 'fa fa-chevron-up',
//                     down: 'fa fa-chevron-down',
//                     previous: 'fa fa-chevron-left',
//                     next: 'fa fa-chevron-right',
//                     today: 'fa fa-calendar-check-o',
//                     clear: 'fa fa-trash',
//                     close: 'fa fa-check primary',
//                 },
//                 calendarWeeks: true,
//                 buttons: {
//                     showToday: false,
//                     showClear: false,
//                     showClose: false,
//                 },
//                 widgetParent: 'body',
//                 keyBinds: null,
//             }, options || {});

//             this.__libInput = 0;
//             // tempusdominus doesn't offer any elegant way to check whether the
//             // datepicker is open or not, so we have to listen to hide/show events
//             // and manually keep track of the 'open' state
//             this.__isOpen = false;
//         },
//     });
// });