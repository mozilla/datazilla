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

        //This is used to store the row to initialize the
        //push log with.  It's set by _adaptData to the first
        //row in the first table loaded.
        this.defaultRowCbSel = "";
        this.defaultRowSelectionSent = false;

        this.cbIdPrefix = 'su_cb_';

        this.scrollHeight = parseInt($(this.tableContainerSel).css('height')) - 125;

        this.datatable = {};
        this.platformInfo = {};
        this.pagenameDataAttr = 'data-pagename';

        this.tableInputClickEvent = 'TABLE_CLICK_EVENT';
        this.gridClickEvent = 'GRID_CLICK_EVENT';
        this.gridMouseoverEvent = 'GRID_MOUSEOVER_EVENT';
        this.closeDataSeriesEvent = 'CLOSE_DATA_SERIES_EVENT';
        this.defaultRowSelectionEvent = 'DEFAULT_ROW_SELECTION_EVENT';

        $(this.eventContainerSel).bind(
            this.gridMouseoverEvent,
            _.bind(this.initializeTestPages, this)
        );

        $(this.eventContainerSel).bind(
            this.gridClickEvent,
            _.bind(this.lockTable, this)
        );

        $(this.eventContainerSel).bind(
            this.closeDataSeriesEvent,
            _.bind(this.uncheckCb, this)
        );

        $(this.tableSel).bind(
            'click', _.bind(this.tableEventHandler, this)
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
        this.platformInfo = eventData.platform_info;

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
                { "sTitle":'', "sWidth":"5px" },
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

            'aaSorting':[ [2, 'asc'] ]
        };


        this._adaptData(datatableOptions, eventData.data);

        this.dataTable = $(this.tableSel).dataTable( datatableOptions );

        //Send default row event out
        if(this.defaultRowSelectionSent === false){

            $(this.eventContainerSel).trigger(
                this.defaultRowSelectionEvent, this.defaultRowCbSel
                );

            this.defaultRowSelectionSent = true;
        }

    },
    lockTable: function(event, eventData){
        $(this.lockTableSel).click();
    },
    uncheckCb: function(event, datumKey){
        var id = this.cbIdPrefix + datumKey;
        $('#' + id).prop("checked", false);
    },
    tableEventHandler: function(event){

        if(event.type == 'click'){

            if( $(event.target).is('input') ){

                var checked = $(event.target).attr('checked');
                var pagename = $(event.target).attr(this.pagenameDataAttr);
                var testSuite = $(this.testSuiteSel).text();
                var platform = $(this.platformSel).text();

                var eventData = {
                    'checked':checked,
                    'pagename':pagename,
                    'testsuite':testSuite,
                    'platform':platform,
                    'platform_info':this.platformInfo
                    };

                $(this.eventContainerSel).trigger(
                    this.tableInputClickEvent, eventData
                    );
            }
        }
    },
    _adaptData: function(datatableOptions, data){

        var adaptedData = [];

        var bars = this.getAlphabeticalSortKeys(data);

        for(var i=0; i<bars.length; i++){

            var datum = data[ bars[i] ];

            var keyData = {
                'pagename':bars[i],
                'testsuite':$(this.testSuiteSel).text(),
                'platform_info':this.platformInfo
                };

            var key = this.cbIdPrefix + MS_PAGE.getDatumKey(keyData);

            if( (i === 0) && (this.defaultRowCbSel === "")){
                this.defaultRowCbSel = '#' + key;
            }

            //page name
            var row = {};
            row['0'] = '<input id="' + key +
                '" type="checkbox" data-pagename="' + bars[i] + '" />';

            row['1'] = bars[i];

            var passFail = 'fail';

            if(datum.test_evaluation){
                passFail = 'pass';

                row['DT_RowClass'] = this.passBackgroundColor;

            }else{

                row['DT_RowClass'] = this.failBackgroundColor;

            }

            row['2'] = passFail;
            row['3'] = datum.mean;
            row['4'] = datum.trend_mean;
            row['5'] = datum.stddev;
            row['6'] = datum.trend_stddev;
            row['7'] = datum.p;
            row['8'] = datum.h0_rejected;
            row['9'] = datum.n_replicates;

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
