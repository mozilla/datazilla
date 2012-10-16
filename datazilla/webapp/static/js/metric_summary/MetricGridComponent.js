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

        if(_.isEmpty(data)){
        }else{
            this.view.initializeGrid(data);
        }
    },
    dataLoadError: function(data, textStatus, jqXHR){

        var messageText = 'Ohhh no, something has gone horribly wrong! ';

        messageText += ' HTTP status:' + data.status + ', ' + textStatus +
        ', ' + data.statusText;

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

        //Data attributes
        this.dataTitlesAttr = 'data-titles';

        //Grid cell container classes
        this.gridColumnHeaderClassSel = '.su-column-headers';
        this.gridRowHeaderClassSel = '.su-row-headers';
        this.gridValuesClassSel = '.su-grid-values';

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

        if(data){
            $(this.testSuiteDashboardContainerSel).css('display', 'block');
        }

        var columns = this.getAlphabeticalSortKeys(
            data.summary_by_platform
            );

        var rows = this.getAlphabeticalSortKeys(
            data.summary_by_test
            );

        var columnTitle, rowTitle = "";

        for(var i=0; i<columns.length; i++){

            columnTitle = columns[i];
            var columnCell = this.getColumnHeaderCell(columnTitle);

            $(this.gridColumnHeaderClassSel).append(columnCell);

        }

        var valueRowWidth = columns.length*30 + columns.length;

        $(this.gridValuesClassSel).css('width', valueRowWidth);

        var scrollWidth = parseInt(
            $('#su_grid_scroll_container').css('width')
            );

        if( (scrollWidth - 60) <= valueRowWidth ){
            $(this.gridScrollContainer).css(
                'width', valueRowWidth*this.gridScrollMultiplier
                );
            $(this.gridScrollBoundary).css(
                'width', valueRowWidth*this.gridScrollMultiplier
                );
        }

        $(this.gridColumnHeaderClassSel).css('width', valueRowWidth);

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

                        this._triggerEvent(
                            this.gridMouseoverEvent, cell
                            );

                        this.triggerDefaultEvent = false;
                    }

                }else{
                    cell = this.getValueCell("");
                }

                $(this.gridValuesClassSel).append(cell);
            }
        }
    },
    getColumnHeaderCell: function(columnTitle){

        var d = $('<div></div>');
        d.addClass(this.gridColumnHeaderClass);
        d.text(columnTitle);

        return d;
    },
    getRowHeaderCell: function(rowTitle){

        var d = $('<div></div>');
        d.addClass(this.gridRowHeaderClass);
        d.text(rowTitle);

        return d;
    },
    getValueCell: function(columnTitle, rowTitle, value){

        var d = $('<div></div>');
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

            this._triggerEvent(
                this.gridClickEvent, cellEl
                );
        }
    },
    _triggerEvent: function(eventType, cell){

        var titles = JSON.parse( $(cell).attr(this.dataTitlesAttr) );

        var data = {};

        if(titles.row_title &&
           titles.column_title &&
           !_.isNull(this.data.tests[titles.row_title])){

            data = this.data.tests[titles.row_title][titles.column_title]['pages'];

        }

        if(!_.isEmpty(data)){

            var eventData = {
                'test':titles.row_title,
                'platform':titles.column_title,
                'data':data
                };

            $(this.eventContainerSel).trigger(
                eventType, eventData
                );
        }
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
