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

        this.scrollHeight = parseInt($(this.tableContainerSel).css('height')) - 125;

        this.datatable = {};

        this.gridClickEvent = 'GRID_CLICK_EVENT';
        this.gridMouseoverEvent = 'GRID_MOUSEOVER_EVENT';

        $(this.eventContainerSel).bind(
            this.gridMouseoverEvent,
            _.bind(this.initializeTestPages, this)
        );

    },

    initializeTestPages: function(event, eventData){

        console.log(eventData);

        $(this.testSuiteSel).text(eventData.test);
        $(this.platformSel).text(eventData.platform);

        var datatableOptions = {
            'bJQueryUI': true,
            'sScrollY':this.scrollHeight,
            //bScrollCollapse:true,
            'sScrollX':"100%",
            'bPaginate': false,
            'bDestroy': true,

            //Double, Double Toil and Trouble
            //see http://www.datatables.net/usage/options sDom for an
            //explanation of the follow line
            //sDom:'<"H"lfr>tC<"F"ip>',

            //bScrollAutoCss: false,
            //bRetrieve:true,

            //Treat search string as regexes
            'oSearch':{ sSearch:"", bRegex:true },
            'xScrollInner':true,
            //iDisplayLength:100,
            'aaData':[],
            'aoColumns':[
                { "sTitle":'page' },
                { "sTitle":'pass/fail' },
                { "sTitle":'mean' },
                { "sTitle":'trend mean' },
                { "sTitle":'std' },
                { "sTitle":'trend std' },
                ],

            'aaSorting':[ [1, 'asc'] ]
        };

        this._adaptData(datatableOptions, eventData.data);

        if(this.datatable){
            $(this.tableSel).die();
            //destroy the table
            //this.datatable.fnClearTable();
            //this.datatable.fnDestroy();
        }
        console.log(datatableOptions);
        this.dataTable = $(this.tableSel).dataTable( datatableOptions );

    },
    _adaptData: function(datatableOptions, data){

        var adaptedData = [];

        var bars = this.getAlphabeticalSortKeys(data);

        var w = this.minWidth*(bars.length/8);
        $(this.barChartContainerSel).css('width', w);

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
