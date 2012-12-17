/*******
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this file,
 * You can obtain one at http://mozilla.org/MPL/2.0/.
 * *****/
var MetricGridComponent = new Class({

    Extends: Component,

    jQuery:'MetricDashboardComponent',

    initialize: function(selector, options){

        this.setOptions(options);

        this.parent(options);

        this.view = new MetricGridView('#MetricGridView',{});

        this.metricSummaryDataEvent = 'METRIC_SUMMARY_EV';

        $(this.view.eventContainerSel).bind(
            this.metricSummaryDataEvent,
            _.bind(
                this.initializeGrid,
                this
                )
            );


    },
    initializeGrid: function(ev, data){
        if(!_.isEmpty(data)){
            this.view.initializeGrid(data);
        }
    }
});
var MetricGridView = new Class({

    Extends:View,

    jQuery:'MetricGridView',

    initialize: function(selector, options){

        this.setOptions(options);

        this.parent(options);

        this.eventContainerSel = '#su_container';
        this.gridSel = '#su_grid';

        //Grid cell classes
        this.gridColumnHeaderClass = 'su-grid-column';
        this.gridRowHeaderClass = 'su-grid-row';
        this.gridValueClass = 'su-grid-value';

        this.guidearrowClassSel = '.su-guidearrow-box';

        //Data attributes
        this.dataTitlesAttr = 'data-titles';

        //Grid cell container classes
        this.gridColumnHeaderClassSel = '.su-column-headers';
        this.gridRowHeaderClassSel = '.su-row-headers';
        this.gridValuesClassSel = '.su-grid-values';

        this.tableContainerSel = '#su_table_container';
        this.lockTableSel = '#su_lock_table';
        this.gridContainerSel = '#su_grid_container';
        this.gridBoundarySel = '#su_boundary';

        this.gridScrollMultiplier = 1.5;
        this.gridScrollContainer = '#su_grid_scroll_container';
        this.gridScrollBoundary = '#su_boundry';

        this.gridSpinnerSel = '#su_grid_spinner';
        this.testSuiteDashboardContainerSel = '#su_test_suite_dashboard';

        this.gridClickEvent = 'GRID_CLICK_EVENT';
        this.gridMouseoverEvent = 'GRID_MOUSEOVER_EVENT';

        this.triggerDefaultEvent = true;

        this.colors = {};
        this.generateColorRamp(
            100, 0xFF7700, 0x44AA00
            );
        //Add color for 0% pass
        this.colors[0] = this.colors[1];

        $(this.gridValuesClassSel).live(
            'click mouseover mouseout mouseenter',
            _.bind(this.gridEventHandler, this)
            );
    },

    initializeGrid: function(data){

        this.data = data;

        $(this.gridSpinnerSel).css('display', 'none');

        var columns, rows = [];

        if(this.data){

            columns = this.getAlphabeticalSortKeys(
                this.data.summary_by_platform
                );

            rows = this.getAlphabeticalSortKeys(
                this.data.summary_by_test
                );

            $(this.testSuiteDashboardContainerSel).css(
                'display', 'block'
                );

            if( (columns.length === 1) && (rows.length === 1) ){
                //If there's only one column and one row there's no need
                //for the grid. Expand the table to 100% of the panel
                this._expandTable(this.data, rows[0], columns[0]);
                return;
            }
        }

        var columnTitle, rowTitle = "";


        var cellWidth = parseInt(
            $('.' + this.gridColumnHeaderClass).css('width')
            );

        //Calculate the width based on total numbers of columns
        //and width of an individual cell
        var valueRowWidth = columns.length*cellWidth + columns.length;

        //Set width of container of individual cells
        $(this.gridValuesClassSel).css('width', valueRowWidth);

        //Set width of container of column labels
        $(this.gridColumnHeaderClassSel).css('width', valueRowWidth);

        var headerWidth = parseInt(
            $(this.gridRowHeaderClassSel).css('width')
            );

        //The width of the scroll container needs to be set dynamically
        //based on the width of all of the rows, row headers, and cell width
        var containerWidth = cellWidth + valueRowWidth + headerWidth;
        $(this.gridScrollContainer).css('width', containerWidth);
        $(this.gridBoundarySel).css('width', containerWidth);

        //Set the column headers
        this._buildGridHeaders(columns);

        //Build the grid of cells
        this._buildGrid(rows, columns, this.data);

    },
    getColumnHeaderCell: function(columnTitle){

        var d = $(document.createElement('div'));
        d.addClass(this.gridColumnHeaderClass);
        d.text(columnTitle);

        return d;
    },
    getRowHeaderCell: function(rowTitle){

        var d = $(document.createElement('div'));
        d.addClass(this.gridRowHeaderClass);
        d.text(rowTitle);

        return d;
    },
    getValueCell: function(columnTitle, rowTitle, value){

        var d = $(document.createElement('div'));
        d.addClass(this.gridValueClass);
        d.text(value);

        var color = '#E8E8E8';

        if(this.colors[value]){
            color = this.colors[value];
        }

        d.css('background-color', color);

        var dataTitles = JSON.stringify(
            { 'column_title':columnTitle, 'row_title':rowTitle }
            );

        d.attr(this.dataTitlesAttr, dataTitles);

        return d;
    },
    generateColorRamp: function(maxSteps, colorBegin, colorEnd){

        var r0 = (colorBegin & 0xff0000) >> 16;
        var g0 = (colorBegin & 0x00ff00) >> 8;
        var b0 = (colorBegin & 0x0000ff) >> 0;

        var r1 = (colorEnd & 0xff0000) >> 16;
        var g1 = (colorEnd & 0x00ff00) >> 8;
        var b1 = (colorEnd & 0x0000ff) >> 0;

        for (var i=1; i <= maxSteps; i++){

            var r = this._interpolateColor(
                r0, r1, i, maxSteps
                );
            var g = this._interpolateColor(
                g0, g1, i, maxSteps
                );

            var b = this._interpolateColor(
                b0, b1, i, maxSteps
                );

            var color = ((( r << 8) | g ) << 8 ) |  b;

            this.colors[i] = '#' + color.toString(16);
        }

    },
    gridEventHandler: function(event){

        var cellEl = $(event.target.outerHTML);
        var id = cellEl.attr('id');

        if(event.type == 'mouseenter'){

            document.body.style.cursor = 'pointer';

        }else if(event.type == 'mouseout'){

            document.body.style.cursor = 'default';

        }else if(event.type == 'mouseover'){

            document.body.style.cursor = 'pointer';

            this._triggerEvent(
                this.gridMouseoverEvent, cellEl
                );

        }else if(event.type == 'click'){

            var checked = $(this.lockTableSel).attr('checked');

            if(checked){
                //table is locked but user has clicked a cell, keep the
                //lock on but change the table to correspnd to the selected
                //cell
                var eventData = this._getCellClickEventData(cellEl);
                MS_PAGE.testPagesComponent.initializeTestPages(
                    this.gridClickEvent, eventData, true
                    );

            } else {
                this._triggerEvent(
                    this.gridClickEvent, cellEl
                    );
            }
        }
    },
    showNoDataMessage: function(){
        $(this.gridSpinnerSel).css('display', 'none');
        $(this.testSuiteDashboardContainerSel).css('display', 'none');
    },
    _expandTable: function(data, test, platform){

        //Hide grid containers
        $(this.gridContainerSel).css('display', 'none');
        $(this.gridSel).css('display', 'none');
        $(this.gridScrollContainer).css('display', 'none');
        $(this.guidearrowClassSel).css('display', 'none');

        //Expand table
        MS_PAGE.testPagesComponent.view.expandTable();

        //Set the table initialization value
        var initializeValue = "";

        if(data.tests[test] && data.tests[test][platform]){
            initializeValue = data.tests[test][platform]['pass']['percent'];
        }

        var initializeCell = this.getValueCell(
            platform, test, initializeValue
            );

        //Trigger initialize event for the one column/row
        this._triggerEvent(
            this.gridMouseoverEvent, initializeCell
            );

    },
    _buildGridHeaders: function(columns){

        for(var i=0; i<columns.length; i++){

            columnTitle = columns[i];
            var columnCell = this.getColumnHeaderCell(columnTitle);

            $(this.gridColumnHeaderClassSel).append(columnCell);
        }
    },
    _buildGrid: function(rows, columns, data){

        for(var r=0; r<rows.length; r++){

            rowTitle = rows[r];
            var rowCell = this.getRowHeaderCell(rowTitle);
            $(this.gridRowHeaderClassSel).append(rowCell);

            for(var c=0; c<columns.length; c++){

                var columnTitle = columns[c];
                var cell;

                if(data.tests[rowTitle][columnTitle]){
                    var value = data.tests[rowTitle][columnTitle]['pass']['percent'];
                    cell = this.getValueCell(columnTitle, rowTitle, value);

                    //This event is only fired once to load a table the
                    //first time the page loads.
                    if(this.triggerDefaultEvent){

                        var platform = MS_PAGE.refData.platform;
                        var test =  MS_PAGE.refData.test;
                        var initializeValue = "";

                        if(data.tests[test] && data.tests[test][platform]){
                            initializeValue = data.tests[test][platform]['pass']['percent'];
                        }

                        if(initializeValue){
                            //URL has test/platform specified, initialize
                            //table to requested data target
                            var initializeCell = this.getValueCell(
                                platform,
                                test,
                                initializeValue
                                );

                            this._triggerEvent(
                                this.gridMouseoverEvent, initializeCell
                                );

                            //Lock the table to the data requested
                            MS_PAGE.testPagesComponent.view.lockTable();

                        }else {
                            //No target table use first defined cell
                            this._triggerEvent(
                                this.gridMouseoverEvent, cell
                                );
                        }

                        this.triggerDefaultEvent = false;
                    }

                }else{
                    cell = this.getValueCell("");
                }

                $(this.gridValuesClassSel).append(cell);
            }
        }

    },
    _triggerEvent: function(eventType, cell){

        var eventData = this._getCellClickEventData(cell);

        $(this.eventContainerSel).trigger(
            eventType, eventData
            );
    },
    _getCellClickEventData: function(cell){

        var titles = JSON.parse( $(cell).attr(this.dataTitlesAttr) );

        var data = {};

        if(titles.row_title &&
           titles.column_title &&
           !_.isNull(this.data.tests[titles.row_title])){

            data = this.data.tests[titles.row_title][titles.column_title]['pages'];

        }

        var eventData = {};

        if(!_.isEmpty(data)){
            eventData = {
                'test':titles.row_title,
                'platform':titles.column_title,
                'platform_info':this.data.tests[titles.row_title][titles.column_title]['platform_info'],
                'data':data
            }
        }

        return eventData;

    },
    _interpolateColor: function(pBegin, pEnd, pStep, pMax){

        if(pBegin < pEnd) {
            return ((pEnd - pBegin) * (pStep/pMax)) + pBegin;
        }else {
            return ((pBegin - pEnd) * (1 - (pStep/pMax))) + pEnd;
        }
    },
    _getColumnRowKeyFromId: function(id){

        var keys = {
            'column_key':'', 'row_key':''
            };

        if(id){
            var keyArray = id.split('SPLIT');

            if(keyArray){
                keys['column_key'] = keyArray[0];
                keys['row_key'] = keyArray[1];
            }
        }

        return keys;
    }

});
