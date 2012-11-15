/*******
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this file,
 * You can obtain one at http://mozilla.org/MPL/2.0/.
 * *****/
var TrendLineComponent = new Class({

    Extends: Component,

    jQuery:'TrendLineComponent',

    initialize: function(selector, options){

        this.setOptions(options);

        this.parent(options);

        this.view = new TrendLineView('#TrendLineView',{});
        this.model = new TrendLineModel('#TrendLineModel',{});

        this.trendLines = {};
        this.trendLineOrder = [];

        //[series index][datapoint index]
        this.seriesIndexToKey = [];
        this.seriesIndexToKey.push([]); //pass series
        this.seriesIndexToKey.push([]); //fail series

        this.tickDisplayDates = {};

        this.plot = undefined;

        this.chartOptions = {
            'grid': {
                'clickable': true,
                'hoverable': true,
                'autoHighlight': true,
                'color': this.view.trendLineColor
            },

            'xaxis': {
                'tickFormatter': _.bind(this.formatLabel, this)
            },

            'yaxis': {
                'autoscaleMargin':0.1
            },

            'hooks': {
                'draw':[this.draw]
            } };


        this.tableInputClickEvent = 'TABLE_CLICK_EVENT';
        this.closeDataSeriesEvent = 'CLOSE_DATA_SERIES_EVENT';

        $(this.view.chartContainerSel).bind(
            'plotclick', _.bind(this._clickPlot, this));

        $(this.view.chartContainerSel).bind(
            'plothover', _.bind(this._hoverPlot, this));

        $(this.view.eventContainerSel).bind(
            this.tableInputClickEvent,
            _.bind(this.initializeTrend, this)
        );

        $(this.view.detailContainerOneSel).live(
            'click mouseover mouseout', _.bind(this.closeDataSeries, this)
            );

    },
    initializeTrend: function(event, eventData){

        this.eventDataReceived = eventData;

        if( eventData.checked ){
            //Load trend line
            this.model.getTrendLine(
                this, this.loadTrendData, this.dataLoadError, eventData
                );

        }else {
            //Remove trend line
            var key = MS_PAGE.getDatumKey(eventData);
            this.deleteDataSeries(key);
        }
    },
    loadTrendData: function(data, response){

        data = this._loadMockData(data);

        this._loadTrendLineData(data);

        var chartData = [];

        //Used to draw circle around the push associated
        //with the revision of interest
        var targetRevisions = [];

        this.tickDisplayDates = {};

        var passSeriesIndex = 0;
        var failSeriesIndex = 1;

        var failDataset = this.getFailDataset();
        var passDataset= this.getPassDataset();

        chartData.push(passDataset);
        chartData.push(failDataset);

        for(var i=0; i<this.trendLineOrder.length; i++){

            var key = this.trendLineOrder[i];

            var passData = [];
            var failData = [];
            var trendData = [];

            var seriesColor = MS_PAGE.passColor;
            var targetRevisionType = 'pass';

            var trendDataset = this.getTrendLineDataset();
            var trendIndex = chartData.push(trendDataset);

            this.seriesIndexToKey[trendIndex - 1] = [];

            var passIndex = 0;
            var failIndex = 0;

            for(var j=0; j<this.trendLines[key]['data'].length; j++){

                if(!this.tickDisplayDates[j]){
                    var unixTimestamp = this.trendLines[key]['data'][j]['date'];
                    var tickLabel = this.convertTimestampToDate(unixTimestamp);
                    this.tickDisplayDates[j] = tickLabel;
                }

                var pageData = this.trendLines[key]['data'][j][
                    'metrics_data'][0]['pages'][
                        this.trendLines[key]['pagename'] ];

                if( pageData.test_evaluation === true ){
                    passIndex = chartData[0].data.push(
                        [ j, parseInt(pageData.mean) ]
                        );
                    this.seriesIndexToKey[0][passIndex -1] = key;
                } else {
                    seriesColor = MS_PAGE.failColor;

                    failIndex = chartData[1].data.push(
                        [ j, parseInt(pageData.mean) ]
                        );

                    this.seriesIndexToKey[1][failIndex - 1] = key;
                }

                var trendDatumIndex = chartData[trendIndex - 1].data.push(
                    [ j, parseInt(pageData.trend_mean) ]
                    );

                this.seriesIndexToKey[trendIndex - 1][trendDatumIndex - 1] = key;

                //revision that is loaded in the page
                if( this.trendLines[key]['data'][j]['dz_revision'] === MS_PAGE.refData.revision ){

                    targetRevisions.push(
                        {'x':j, 'y':parseInt(pageData.mean) }
                        );

                    if( pageData.test_evaluation === true ){
                        this.trendLines[key].datapoint_plot_location.point_index = passIndex - 1;
                    } else {
                        targetRevisionType = 'fail';
                        this.trendLines[key].datapoint_plot_location.point_index = failIndex - 1;
                    }
                }
            }

            if(targetRevisionType === 'pass'){
                this.trendLines[key].datapoint_plot_location.series_index = passSeriesIndex;
            }else{
                this.trendLines[key].datapoint_plot_location.series_index = failSeriesIndex;
            }

            var rgbAlpha = this.view.loadSeriesLabelContainer(
                key, this.trendLines[key], seriesColor
                );

            this.trendLines[key].rgb_alpha = rgbAlpha;

        }

        this.plot = $.plot(
            $(this.view.chartContainerSel),
            chartData,
            this.chartOptions);

        this.view.drawCircleAroundDataPoints(targetRevisions, this.plot);

    },
    getFailDataset: function(){
        return {
                'data':[],
                'points': { 'show': true },
                'color': MS_PAGE.failColor
                };
    },
    getPassDataset: function(){
        return {
                'data':[],
                'points': { 'show': true },
                'color': MS_PAGE.passColor
                };
    },
    getTrendLineDataset: function(){
        return {
                'data':[],
                'lines': { 'show': true },
                'color': this.view.trendLineColor
                };
    },
    convertTimestampToDate: function(unixTimestamp){
        var dateObj = new Date(unixTimestamp * 1000);
        var dateString = dateObj.getFullYear() + '-' +
            (dateObj.getMonth() + 1) + '-' +
            dateObj.getDate() + ' ' +
            dateObj.getHours() + ':' +
            dateObj.getMinutes() + ':' +
            dateObj.getSeconds();
        return dateString;
    },
    formatLabel: function(label, series){
        return this.tickDisplayDates[label];
    },
    closeDataSeries: function(event){

        if(event.type === 'click'){

            var closeIcon = $(event.target).hasClass(
                this.view.closeIconClassName
                );

            if(closeIcon){

                var key = this._getKeyFromEventTarget(event.target);
                this.deleteDataSeries(key);

                $(this.view.eventContainerSel).trigger(
                    this.closeDataSeriesEvent, key
                    );
            }

        }else if(event.type === 'mouseover'){

            var key = this._getKeyFromEventTarget(event.target);

            if(key){

                this.plot.highlight(
                    this.trendLines[key].datapoint_plot_location.series_index,
                    this.trendLines[key].datapoint_plot_location.point_index
                    );
            }

        }else if(event.type === 'mouseout'){
            var key = this._getKeyFromEventTarget(event.target);

            if(key){
                this.plot.unhighlight(
                    this.trendLines[key].datapoint_plot_location.series_index,
                    this.trendLines[key].datapoint_plot_location.point_index
                    );
            }
        }
    },
    deleteDataSeries: function(key){

        var intKey = parseInt(key);
        for(var i=0; i<this.trendLineOrder.length; i++){
            //Data series found, delete it
            if( intKey === this.trendLineOrder[i] ){

                delete(this.trendLineOrder[i]);
                this.trendLineOrder = _.compact(this.trendLineOrder);

                delete(this.trendLines[key]);
                this.view.closeDataSeries(key);

                break;
            }
        }

        this.loadTrendData([], {});
    },
    _getKeyFromEventTarget: function(etarget){

        var sel =  '[id*="' + this.view.legendIdPrefix + '"]';
        var el = $(etarget).closest(sel);
        var key = "";

        if(el.length){
            var id = $(el).attr('id');
            key = id.replace(this.view.legendIdPrefix, '');
        }

        return key;
    },
    _hoverPlot: function(event, pos, item){

        if(item){

            var key = this.seriesIndexToKey[item.seriesIndex][item.dataIndex];

            if(key != this.hoverLegendKey){
                var lastKey = this.hoverLegendKey || key;
                //User has hovered directly from a point on series a
                //to a point on series b, we need to set the point on
                //series a back to the appropriate background color
                this.view.unhighlightLegend(
                    this.trendLines[lastKey].rgb_alpha,
                    this.hoverLegendEl
                    );
            }

            this.hoverLegendKey = key;

            var datum = this.trendLines[key]['data'][ item.datapoint[0] ];

            var keyValueArray = [];
            var platform = this.trendLines[key]['platform'];
            var pagename = this.trendLines[key]['pagename'];

            var id = this.view.getSeriesId(key);
            var legendEl = $('#' + id);

            this.hoverLegendEl = legendEl;

            this.view.highlightLegend(legendEl);

            var metricKeys = [
                'mean', 'trend_mean', 'stddev', 'trend_stddev',
                'p', 'fdr', 'h0_rejected', 'n_replicates' ];

            keyValueArray.push(
                {'label':'dz_revision',
                 'value':[datum.dz_revision]});

            keyValueArray.push(
                {'label':'date',
                 'value':[this.convertTimestampToDate(datum.date)]});

            keyValueArray.push(
                {'label':'branch',
                 'value':[datum.branch_name]});

            keyValueArray.push(
                {'label':'test suite',
                 'value':[datum.metrics_data[0]['testrun']['suite'] ]});

            keyValueArray.push(
                {'label':'page',
                 'value':[pagename]});

            for(var i=0; i<metricKeys.length; i++){

                var mk = metricKeys[i];
                keyValueArray.push(
                    {'label':mk,
                     'value':[datum.metrics_data[0]['pages'][pagename][mk] ] });
            }

            if(datum.revisions.length > 1){
                keyValueArray.push(
                    {'label':'revisions',
                    'value':datum.revisions});
            }

            var url = this.model.getRawDataUrl(this.trendLines[key]);

            var color = MS_PAGE.passColor;
            if( datum.metrics_data[0]['pages'][pagename]['test_evaluation'] === false ){
                color = MS_PAGE.failColor;
            }

            var rgbAlpha = this.view.hexToRgb(color);

            this.view.loadDatumLabelContainer(
                keyValueArray, url, rgbAlpha, color
                );
        } else {

            if(this.hoverLegendKey && this.hoverLegendEl){

                this.view.unhighlightLegend(
                    this.trendLines[this.hoverLegendKey].rgb_alpha,
                    this.hoverLegendEl
                    );

                this.hoverLegendKey = undefined;
                this.hoverLegendEl = undefined;
            }
        }
    },
    _clickPlot: function(event, pos, item){
        if(item){
            var key = this.seriesIndexToKey[item.seriesIndex][item.dataIndex];
        }
    },
    _loadTrendLineData: function(data){

        if(data.length > 0){

            var key = MS_PAGE.getDatumKey(this.eventDataReceived);

            if(!this.trendLines[key]){
                this.trendLineOrder.push(key);

                this.trendLines[key] = {
                    pagename:this.eventDataReceived.pagename,
                    testsuite:this.eventDataReceived.testsuite,
                    platform:this.eventDataReceived.platform,
                    platform_info:this.eventDataReceived.platform_info,
                    data:data,
                    rgb_alpha:"",
                    datapoint_plot_location:{
                        'series_index':0, 'point_index':0
                        }
                    };
            }
        }
    },
    _loadMockData: function(data){

        var datum = {};
        var datumIndex = 0;

        for(var i=0; i<data.length; i++){
            if( data[i]['metrics_data'].length > 0 ){
                datum = data[i];
                datumIndex = i;
            }
        }
        for(var i=0; i<data.length; i++){
            if( datumIndex != i ){

                var datumClone = jQuery.extend(true, {}, datum);
                var mean = parseInt(datumClone['metrics_data'][0].pages[ this.eventDataReceived.pagename ].mean);
                var trendMean = parseInt(datumClone['metrics_data'][0].pages[ this.eventDataReceived.pagename ].trend_mean);

                //mean = Math.floor(Math.random() * (mean - (mean - 5) + 1)) + (mean - 5);
                //trendMean = Math.floor(Math.random() * (trendMean - (trendMean - 5) + 1)) + (trendMean - 5);

                datumClone['metrics_data'][0].pages[ this.eventDataReceived.pagename ].mean = parseInt(mean);
                datumClone['metrics_data'][0].pages[ this.eventDataReceived.pagename ].trend_mean = parseInt(trendMean);
                datumClone['metrics_data'][0].pages[ this.eventDataReceived.pagename ].test_evaluation = true;

                datumClone.dz_revision = 'SomeOtherRevision';

                data[i] = datumClone;
            }
            var pushlogId = parseInt(datumClone['metrics_data'][0].pages[ this.eventDataReceived.pagename ]['pushlog_id']);
            datumClone['metrics_data'][0].pages[ this.eventDataReceived.pagename ]['pushlog_id'] = pushlogId + i;
        }

        return data;
    },

    dataLoadError: function(data, textStatus, jqXHR){

        var messageText = 'Ohhh no, something has gone horribly wrong! ';

        messageText += ' HTTP status:' + data.status + ', ' + textStatus +
        ', ' + data.statusText;

    }
});
var TrendLineView = new Class({

    Extends:View,

    jQuery:'TrendLineView',

    initialize: function(selector, options){

        this.setOptions(options);

        this.parent(options);

        this.eventContainerSel = '#su_container';
        this.chartContainerSel = '#su_trendline_plot';
        this.detailContainerOneSel = '#su_graph_detail_container_1';

        this.datumRevision = '#su_datum_revision';
        this.datumRawDataAnchor = '#su_raw_data';
        this.detailContainerTwoSel = '#su_graph_detail_container_2';
        this.datumControls = '#su_datum_controls';

        this.datumDisplayContainers = [
            this.datumRevision, this.datumControls,
            this.detailContainerTwoSel ];

        this.datasetLegendSel = '#su_legend';
        this.datasetTitleName = 'su_dataset_title';
        this.datasetCbContainerName = 'su_dataset_cb';
        this.datasetCloseName = 'su_dataset_close';
        this.legendIdPrefix = 'su_detail_';

        this.closeIconClassName = 'ui-icon-close';

        this.trendLineColor = '#A9A9A9';

        this.displayedSeriesLabel = {};

    },

    drawCircleAroundDataPoints: function(targetRevisions, plot){

        var ctx = plot.getCanvas().getContext("2d");

        for(var i=0; i<targetRevisions.length; i++){

            var dataPoint = targetRevisions[i];

            var o = plot.pointOffset({ 'x':dataPoint.x, 'y':dataPoint.y });

            o.left += 0.5;
            ctx.moveTo(o.left, o.top);
            ctx.beginPath();
            ctx.arc(o.left, o.top, 10, 2*Math.PI, false);
            ctx.stroke();
        }

    },
    loadSeriesLabelContainer: function(key, data, hexColor, fnCloseDataset){

        var rgbAlpha = this.hexToRgb(hexColor);

        if(this.displayedSeriesLabel[key] === true){
            //already displayed
            return rgbAlpha;
        }

        var label = data['testsuite'] + ' ' +
                    data['pagename'] + ' ' +
                    data['platform'];

        //Add alpha channel to lighten the color
        var legendClone = $(this.datasetLegendSel).clone();

        var id = this.getSeriesId(key);
        $(legendClone).attr('id', id);

        var titleDiv = $(legendClone).find(
            '[name="' + this.datasetTitleName + '"]'
            );

        var label = data.testsuite + ' ' +
            data.pagename + ' ' + data.platform;

        $(titleDiv).text( label );

        $(legendClone).css('background-color', rgbAlpha);
        $(legendClone).css('border-color', hexColor);
        $(legendClone).css('border-width', 1);
        $(legendClone).css('display', 'block');

        //Cannot set the div hover style in css only because the
        //explicit setting of background-color seems to over ride
        //the hover style.
        $(legendClone).hover(
            function(){
                //On mouseOver
                $(this).css('background-color', '#FFFFFF');
            },
            function(){
                //On mouseOut
                $(this).css('background-color', rgbAlpha);
            }
        );

        $(this.detailContainerOneSel).append(legendClone);

        this.displayedSeriesLabel[key] = true;

        return rgbAlpha;
    },
    loadDatumLabelContainer: function(datumKeyValues, url, rgbAlpha, color){

        $(this.detailContainerTwoSel).empty();

        var datumTable = $(document.createElement('table'));

        $(this.datumRawDataAnchor).attr('href', url);
        $(this.datumRawDataAnchor).button();

        for(var i=0; i<this.datumDisplayContainers.length; i++){
            var sel = this.datumDisplayContainers[i];
            $(sel).css('background-color', rgbAlpha);
            $(sel).css('border-color', color);
            //$(sel).css('border-width', 2);
        }

        for(var i=0; i<datumKeyValues.length; i++){

            var datum = datumKeyValues[i];
            var label = datum['label'];
            var values = datum['value'];

            if(label === 'dz_revision'){
                $(this.datumRevision).text(values[0]);
                continue;
            }

            var rowspan = datumKeyValues[i].length;

            var tr = $(document.createElement('tr'));
            var th = $(document.createElement('th'));
            $(th).text(label);
            $(th).css('text-align', 'right');
            $(th).addClass('su-light-text');
            $(tr).append(th);

            $(th).attr('rowspan', rowspan);

            for(var j=0; j<values.length; j++){

                var td = $(document.createElement('td'));
                $(td).css('text-align', 'right');
                $(td).text(values[j]);

                if(j === 0){
                    $(tr).append(td);
                    $(datumTable).append(tr);
                }else{
                    var newRow = $(document.createElement('tr'));
                    var emptyTd = $(document.createElement('td'));
                    $(newRow).append(emptyTd);
                    $(newRow).append(td);
                    $(datumTable).append(newRow);
                }
            }
        }

        $(this.detailContainerTwoSel).append(datumTable);
    },
    getSeriesId: function(key){
        return this.legendIdPrefix + key;
    },
    highlightLegend: function(el){
        if(el){
            $(el).css('background-color', '#FFFFFF');
        } else {
            $(this).css('background-color', '#FFFFFF');
        }
    },
    unhighlightLegend: function(rgbAlpha, el){

        if(el){
            $(el).css('background-color', rgbAlpha);
        } else {
            $(this).css('background-color', rgbAlpha);
        }
    },
    hexToRgb: function(hex) {
        var result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        var rgbAlpha = 'rgba(' + parseInt(result[1], 16) + ',' +
            parseInt(result[2], 16) + ',' +
            parseInt(result[3], 16) + ',0.1)';

        return rgbAlpha;
    },
    closeDataSeries: function(key){
        $('#' + this.legendIdPrefix + key).remove();
        delete(this.displayedSeriesLabel[key]);
    }

});

var TrendLineModel = new Class({

    Extends:Model,

    jQuery:'TrendLineModel',

    initialize: function(options){

        this.setOptions(options);

        this.parent(options);

    },
    getTrendLine: function(context, fnSuccess, fnError, eventData){

        var url = this.getMetricsUrl(eventData, 20, 3);

        jQuery.ajax( url, {
            accepts:'application/json',
            dataType:'json',
            cache:false,
            type:'GET',
            context:context,
            error:fnError,
            success:fnSuccess,
        });
    },
    getMetricsUrl: function(data, pushesBefore, pushesAfter){

        var url = '/' + MS_PAGE.refData.project +
            '/testdata/metrics/' + MS_PAGE.refData.branch + '/' +
            MS_PAGE.refData.revision + '/pushlog';

        url = this.getUri(data, url);

        url += '&pushes_before=' + pushesBefore;
        url += '&pushes_after=' + pushesAfter;

        return url;
    },
    getRawDataUrl: function(data){

        var url = '/' + MS_PAGE.refData.project +
            '/testdata/raw/' + MS_PAGE.refData.branch + '/' +
            MS_PAGE.refData.revision;

        url = this.getUri(data, url);

        return url;

    },
    getUri: function(data, url){

        url += '?os_name=' + data.platform_info.operating_system_name;
        url += '&os_version=' + data.platform_info.operating_system_version;
        url += '&processor=' + data.platform_info.processor;
        url += '&build_type=' + data.platform_info.type;
        url += '&test_name=' + data.testsuite;
        url += '&page_name=' + data.pagename;

        return url;
    }

});
