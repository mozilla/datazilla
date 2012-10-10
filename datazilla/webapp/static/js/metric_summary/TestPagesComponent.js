/*******
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this file,
 * You can obtain one at http://mozilla.org/MPL/2.0/.
 * *****/
var TestPagesComponent = new Class({

    Extends: Component,

    jQuery:'TestPagesComponent',

    initialize: function(selector, options){

        this.setOptions(options);

        this.parent(options);

        this.view = new TestPagesView('#TestPagesView',{});
        this.model = new TestPagesModel('#TestPagesModel',{});

    },
    initializeTestPages: function(ev, data){

        if(_.isEmpty(data)){

        }else{
            this.view.initializeTestPages(data);
        }
    }
});
var TestPagesView = new Class({

    Extends:View,

    jQuery:'TestPagesView',

    initialize: function(selector, options){

        this.setOptions(options);

        this.parent(options);

        this.eventContainerSel = '#su_container';
        this.tableContainerSel = '#su_table_container';
        this.tableSel = '#su_test_pages';
        this.testSuiteSel = '#su_test_suite';
        this.platformSel = '#su_platform';

        this.platformSel = '#su_platform';
        this.lockTableSel = '#su_lock_table';

        this.failBackgroundColor = 'su-fail-background-color';
        this.passBackgroundColor = 'su-pass-background-color';

        this.lastMouseOverRow = "";

        this.scrollHeight = parseInt($(this.tableContainerSel).css('height')) - 125;

        this.datatable = {};

        this.gridClickEvent = 'GRID_CLICK_EVENT';
        this.gridMouseoverEvent = 'GRID_MOUSEOVER_EVENT';

        $(this.eventContainerSel).bind(
            this.gridMouseoverEvent,
            _.bind(this.initializeTestPages, this)
        );

        $(this.eventContainerSel).bind(
            this.gridClickEvent,
            _.bind(this.lockTable, this)
        );

        $(this.lockTableSel).bind('click', function(event){
            var checked = $(event.eventTarget).attr('checked');
            console.log('checked:' + checked);
        });

        $(this.tableSel).live(
            'click mouseover', _.bind(this.tableEventHandler, this)
        );
    },

    initializeTestPages: function(event, eventData){

        var checked = $(this.lockTableSel).attr('checked');

        //User has locked the table
        if(checked){
            return;
        }

        $(this.testSuiteSel).text(eventData.test);
        $(this.platformSel).text(eventData.platform);

        var datatableOptions = {

            'bJQueryUI': true,
            'sScrollY':this.scrollHeight,
            'sScrollX':"100%",
            'bPaginate': false,
            'bDestroy': true,

            //search string is interpreted as a regex
            'oSearch':{ sSearch:"", bRegex:true },
            'xScrollInner':true,

            'iDisplayLength':100,

            'aaData':[],

            'aoColumns':[
                { "sTitle":'page', "sWidth":"75px" },
                { "sTitle":'p/f', "sWidth":"30px" },
                { "sTitle":'mean', "sWidth":"45px" },
                { "sTitle":'trend mean', "sWidth":"70px" },
                { "sTitle":'std', "sWidth":"40px" },
                { "sTitle":'trend std', "sWidth":"70px" },
                { "sTitle":'p value', "sWidth":"60px" },
                { "sTitle":'h0 rejected', "sWidth":"75px" },
                { "sTitle":'replicates', "sWidth":"75px" },
                ],

            'aaSorting':[ [1, 'asc'] ]
        };

        this._adaptData(datatableOptions, eventData.data);

        this.dataTable = $(this.tableSel).dataTable( datatableOptions );

    },
    lockTable: function(event, eventData){
        $(this.lockTableSel).click();
    },
    tableEventHandler: function(event){
        if(event.type == 'mouseover'){

            var target = $(event.target);
            var elParent = $(target).parent();
            console.log( $(elParent).hasClass('su-fail-background-color') );

            var highlightClass = "";

            $(elParent).removeClass('odd');
            $(elParent).removeClass('even');

            console.log($(elParent));
            if( $(elParent).hasClass(this.passBackgroundColor) ){

                $(elParent).removeClass(this.passBackgroundColor);
                $(elParent).addClass('su-pass-hl-color');

                this._resetRowHighlight(elParent, this.passBackgroundColor);

            }else if( $(elParent).hasClass(this.failBackgroundColor) ){

                $(elParent).removeClass(this.failBackgroundColor);
                $(elParent).addClass('su-fail-hl-color');

                this._resetRowHighlight(elParent, this.failBackgroundColor);

            }
        }
    },
    _resetRowHighlight: function(el, colorClass){

        if(this.lastMouseOverRow){

            $(this.lastMouseOverRow).removeClass('su-pass-hl-color');
            $(this.lastMouseOverRow).removeClass('su-fail-hl-color');

            //$(this.lastMouseOverRow).addClass(colorClass);
        }

        this.lastMouseOverRow = el;
    },
    _adaptData: function(datatableOptions, data){

        var adaptedData = [];

        var bars = this.getAlphabeticalSortKeys(data);

        for(var i=0; i<bars.length; i++){

            var datum = data[ bars[i] ];

            //page name
            var row = {};
            row['0'] = bars[i];

            var passFail = 'fail';

            if(datum.test_evaluation){
                passFail = 'pass';

                row['DT_RowClass'] = 'su-pass-background-color';

            }else{

                row['DT_RowClass'] = 'su-fail-background-color';

            }

            row['1'] = passFail;
            row['2'] = datum.mean;
            row['3'] = datum.trend_mean;
            row['4'] = datum.stddev;
            row['5'] = datum.trend_stddev;
            row['6'] = datum.p;
            row['7'] = datum.h0_rejected;
            row['8'] = datum.n_replicates;

            datatableOptions.aaData.push( row );
        }
    }
});

var TestPagesModel = new Class({

    Extends:Model,

    jQuery:'TestPagesModel',

    initialize: function(options){

        this.setOptions(options);

        this.parent(options);

    }
});
