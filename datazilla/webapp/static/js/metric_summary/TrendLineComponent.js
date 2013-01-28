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

        //Holds all trend line data loaded
        this.trendLines = {};
        //Maintains the trend line load order according
        //to the order the user loads them
        this.trendLineOrder = [];

        //Maps the flot series index to the trendline keys
        //and allows flot callback functions to map to the
        //corresponding reference data in this.trendLines
        this.seriesIndexToKey = [];


        //pass series
        this.passSeriesIndex = this.seriesIndexToKey.push([]) - 1;
        //fail series
        this.failSeriesIndex = this.seriesIndexToKey.push([]) - 1;
        //no data series
        this.noMetricsDataSeriesIndex = this.seriesIndexToKey.push([]) - 1;

        this.tickDisplayDates = {};

        this.trendLineAdapters = {
            'least_squares_fit':this.getLeastSquaresFit
            };

        //Maps the 'compared to' revision to the corresponding
        //plot datapoint index
        this.revisionToPlotIndex = {};

        //Holds all event data received. It's used for
        //reloading all series data with updated pushes
        //before and after values.
        this.eventData = [];

        this.pushesBefore = 25;
        this.pushesAfter = 10;

        //true indicates push retrieval in progress
        //false indicates more pushes can be retrieved
        this.getPushState = false;

        //The first simulated table checkbox click will
        //not have the eventData.checked attribute set.  This
        //switch allows initializeTrend to fully process the
        //event anyway.  Not sure why the .click() function
        //does not take care of this.
        this.simulatedTableCBClick = false;

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
                'autoscaleMargin':0.3
            },

            'series': {

                'points': {
                    'radius': 2.5
                }
            },

            'selection':{
                'mode':'x',
                'color':'#BDBDBD'
            },

            'hooks': {
                'draw':[this.draw]
            } };


        this.tableInputClickEvent = 'TABLE_CLICK_EVENT';
        this.closeDataSeriesEvent = 'CLOSE_DATA_SERIES_EVENT';
        this.defaultRowSelectionEvent = 'DEFAULT_ROW_SELECTION_EVENT';

        $(this.view.chartContainerSel).bind(
            'plotclick', _.bind(this._clickPlot, this)
            );

        $(this.view.chartContainerSel).bind(
            'plothover', _.bind(this._hoverPlot, this)
            );

        $(this.view.chartContainerSel).bind(
            'plotselected', _.bind(this._selectPlot, this)
            );

        $(this.view.eventContainerSel).bind(
            this.tableInputClickEvent,
            _.bind(this.initializeTrend, this)
        );

        $(this.view.getPushesSel).bind(
            'click', _.bind(this.getPushes, this)
            );

        $(this.view.detailContainerOneSel).live(
            'click mouseover mouseout', _.bind(this.closeDataSeries, this)
            );

        $(this.view.pushesBeforeSel).bind(
            'keyup', _.bind(this._handlePushAroundInput, this)
            );

        $(this.view.pushesAfterSel).bind(
            'keyup', _.bind(this._handlePushAroundInput, this)
            );

        $(this.view.trendLineDisplaySel).bind(
            'change', _.bind(this.redrawTrendLine, this)
            );

        //Set the push counts in the HTML
        this.view.setPushCounts(this.pushesBefore, this.pushesAfter);

        //Simulate click on the default test suite table row
        $(this.view.eventContainerSel).bind(
            this.defaultRowSelectionEvent,
            _.bind(this.clickTableCB, this)
            );

        //Initialize the push selection range to empty strings
        this.view.setPushRange("", "", "");

    },
    clickTableCB: function(event, eventData){

        this.simulatedTableCBClick = true;
        $(eventData).click();

    },
    initializeTrend: function(event, eventData){

        if(this.simulatedTableCBClick === true){
            eventData.checked = 'checked';
            this.simulatedTableCBClick = false;
        }

        if( eventData.checked ){
            //Load trend line
            var key = MS_PAGE.getDatumKey(eventData);

            this.trendLineOrder.push(key);

            var pushCounts = this.view.getPushCounts();

            this.setGetPushState();

            this.model.getTrendLine(
                this, this.loadTrendData, eventData,
                pushCounts.before, pushCounts.after
                );

        }else {
            //Remove trend line
            var key = MS_PAGE.getDatumKey(eventData);
            this.deleteDataSeries(key);
        }
    },
    getPushes: function(event){

        var pushCounts = this.view.getPushCounts();

        for(var i=0; i<this.trendLineOrder.length; i++){

            var key = this.trendLineOrder[i];

            this.setGetPushState();

            //Build the eventData data structure
            //for each trend line
            var trendLineEventData = {};
            trendLineEventData.pagename = this.trendLines[key].pagename;
            trendLineEventData.testsuite = this.trendLines[key].testsuite;
            trendLineEventData.platform = this.trendLines[key].platform;
            trendLineEventData.platform_info = this.trendLines[key].platform_info;

            this.model.getTrendLine(
                this, this.loadTrendData, trendLineEventData,
                pushCounts.before, pushCounts.after
                );
        }
    },
    setGetPushState: function(){

        this.getPushState = true;
        this.view.setGetPushState();

    },
    unsetGetPushState: function(){

        this.getPushState = false;
        this.view.unsetGetPushState();

    },
    loadTrendData: function(data, response, eventData){

        this._loadTrendLineData(data, eventData);

        var chartData = [];

        //Used to draw circle around the push associated
        //with the revision of interest
        var targetRevisions = [];

        this.tickDisplayDates = {};

        //flot data item to be passed to hoverPlot
        var flotItem = {};

        var failDataset = this.getFailDataset();
        var passDataset= this.getPassDataset();
        var noDataDataset= this.getNoDataDataset();

        chartData[this.passSeriesIndex] = passDataset;
        chartData[this.failSeriesIndex] = failDataset;
        chartData[this.noMetricsDataSeriesIndex] = noDataDataset;

        var displayType = $(this.view.trendLineDisplaySel).val();
        trendAdapter = this.trendLineAdapters[displayType];

        /****
         * This loop populates chartData for flot.  Data types that need to
         * be colored/treated differently (pass, fail, no data, trend data)
         * all need to be their own series.  This gives the appearance of
         * individual data points being "colored" differently, when they are
         * actually different series color assignments in flot.
         * This is a bit counter intuitive but unfortunately, the flot data
         * structure does not support assigning different colors to data
         * points individually.
         ****/
        for(var i=0; i<this.trendLineOrder.length; i++){

            var key = this.trendLineOrder[i];

            var passData = [];
            var failData = [];
            var trendData = [];

            var seriesColor = '';
            var targetRevisionType = 'pass';
            var dzRevision = '';

            //A new trend dataset needs to be created for each trend line
            //since it is displayed as a line, otherwise flot will display
            //a disjointed line connected across all data series.  The other
            //data series types (fail, pass, noData) are displayed as points
            //so they need to share the dataset array.
            var trendDataset = this.getTrendLineDataset();
            var trendIndex = chartData.push(trendDataset) - 1;

            this.seriesIndexToKey[trendIndex] = [];

            var passDatumIndex = 0;
            var failDatumIndex = 0;
            var noDataDatumIndex = 0;

            var trendMeanValue = 0;

            var metricsData = [];
            var trendAdapterValues = [[], []];

            for(var j=0; j<this.trendLines[key]['data'].length; j++){

                metricsData = this.trendLines[key]['data'][j]['metrics_data'];

                dzRevision = this.trendLines[key]['data'][j]['dz_revision'];

                //Store x axis tick labels
                if(!this.tickDisplayDates[j]){

                    var tickLabel = "";

                    //Exclude first and last tick labels on the x-axis
                    //to keep things unclutered
                    if((j > 0) && (j <this.trendLines[key]['data'].length - 1)){
                        var unixTimestamp = this.trendLines[key]['data'][j]['date'];
                        tickLabel = this.view.convertTimestampToDate(
                            unixTimestamp, false
                            );
                    }

                    this.tickDisplayDates[j] = tickLabel;
                }

                if(metricsData.length > 0){
                    var pageData =
                        metricsData[0]['pages'][this.trendLines[key]['pagename'] ];

                    //Metrics data is available set trend datum
                    trendMeanValue = parseInt(pageData.trend_mean);
                    var trendDatumIndex = chartData[trendIndex].data.push(
                        [ j, trendMeanValue ]
                        ) - 1;

                    if(trendAdapter){
                        trendAdapterValues[0].push(j);
                        trendAdapterValues[1].push(trendMeanValue);
                    }

                    this.seriesIndexToKey[trendIndex][trendDatumIndex] = key;

                    if( pageData.test_evaluation === true ){

                        //Test passed
                        passDatumIndex = chartData[this.passSeriesIndex].data.push(
                            [ j, parseInt(pageData.mean) ]
                            ) - 1;

                        this.seriesIndexToKey[this.passSeriesIndex][passDatumIndex] = key;

                        if(dzRevision && (!this.revisionToPlotIndex[dzRevision])){
                            this.revisionToPlotIndex[dzRevision] = passDatumIndex;
                        }

                    } else if(pageData.test_evaluation === false) {

                        //Test failed
                        failDatumIndex = chartData[this.failSeriesIndex].data.push(
                            [ j, parseInt(pageData.mean) ]
                            ) - 1;

                        this.seriesIndexToKey[this.failSeriesIndex][failDatumIndex] = key;

                        if(dzRevision && (!this.revisionToPlotIndex[dzRevision])){
                            this.revisionToPlotIndex[dzRevision] = failDatumIndex;
                        }

                    }

                    //revision that is loaded in the page
                    if( this.trendLines[key]['data'][j]['dz_revision'] ===
                        MS_PAGE.refData.revision ){

                        targetRevisions.push(
                            {'x':j, 'y':parseInt(pageData.mean) }
                            );

                        //flot datapoint object of the target revision
                        flotItem.datapoint = [
                            j, pageData.mean
                            ];

                        if( pageData.test_evaluation === true ){

                            //Set the series color
                            seriesColor = MS_PAGE.passColor;

                            //Record the datum point index
                            this.trendLines[key].datapoint_plot_location.point_index = passDatumIndex;

                            //Set flot seriesIndex and dataIndex attributes
                            flotItem.seriesIndex = this.passSeriesIndex;
                            flotItem.dataIndex =
                                this.trendLines[key].datapoint_plot_location.point_index;

                        } else {
                            //Set the revision type to fail, it's pass by
                            //default
                            targetRevisionType = 'fail';

                            //Set the series color
                            seriesColor = MS_PAGE.failColor;

                            //Record the datum point index
                            this.trendLines[key].datapoint_plot_location.point_index = failDatumIndex;

                            //Set flot seriesIndex and dataIndex attributes
                            flotItem.seriesIndex = this.failSeriesIndex;
                            flotItem.dataIndex =
                                this.trendLines[key].datapoint_plot_location.point_index;

                        }
                    }

                } else {
                    //No metrics data is available, color gray and place
                    //on trend line
                    noDataDatumIndex = chartData[this.noMetricsDataSeriesIndex].data.push(
                        [ j, parseInt(this.trendLines[key]['mean']) ]
                        ) - 1;

                    this.seriesIndexToKey[this.noMetricsDataSeriesIndex][noDataDatumIndex] = key;
                }
            } //end data for loop

            //Set the series_index for the datapoint plot location
            if(targetRevisionType === 'pass'){
                this.trendLines[key].datapoint_plot_location.series_index = this.passSeriesIndex;
            }else{
                this.trendLines[key].datapoint_plot_location.series_index = this.failSeriesIndex;
            }

            //Get the rgb alpha for the series label
            var rgbAlpha = this.view.loadSeriesLabelContainer(
                key, this.trendLines[key], seriesColor
                );

            //Store the rgb alpha for hover events
            this.trendLines[key].rgb_alpha = rgbAlpha;

            //If a trend data adapter has been selected
            //use it to process the trend data and set the chartData
            //to display to the adapter's return value
            if(trendAdapter){
                var adaptedLine = trendAdapter(
                    trendAdapterValues[0], trendAdapterValues[1]
                    );

                chartData[trendIndex].data = adaptedLine;
            }
        } //end trend line for loop

        //Hide the per-push spinner
        this.unsetGetPushState();

        //Display the chart
        this.view.displayDashboard();

        //Initialize the plot with the chartData
        this.plot = $.plot(
            $(this.view.chartContainerSel),
            chartData,
            this.chartOptions);

        //Set hover datum to the revision of interest.
        //Tell hoverPlot to not highlight datum hovered
        //by passing the boolean "true" parameter.  There is
        //an issue in flot that causes the first highlighted
        //point to be off on the y-axis.  This is a work around.
        this._hoverPlot({}, {}, flotItem, true);

        //Draw a circle around the target revisions that the
        //page is loaded on to help the user find their push
        //of interest
        this.view.drawCircleAroundDataPoints(targetRevisions, this.plot);

    },
    redrawTrendLine: function(){

        this.loadTrendData([], {});

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
    getNoDataDataset: function(){

        return {
                'data':[],
                'points': { 'show': true },
                'color': this.view.trendLineColor
                };
    },
    getTrendLineDataset: function(){

        return {
                'data':[],
                'lines': { 'show': true },
                'color': this.view.trendLineColor
                };
    },
    formatLabel: function(label, series){

        return this.tickDisplayDates[label] || "";
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

        //Redraw trend lines
        this.redrawTrendLine();
    },
    getLeastSquaresFit: function(valuesX, valuesY){

        var sumX = 0;
        var sumY = 0;
        var sumXY = 0;
        var sumXX = 0;
        var  x = 0;
        var y = 0;
        var count = 0;

        var totalValues = valuesX.length;
        if(totalValues === 0){
            return [];
        }

        for(var i=0; i < totalValues; i++){
            x = valuesX[i];
            y = valuesY[i];

            sumX += x;
            sumY += y;
            sumXX += x*x;
            sumXY += x*y;
        }

        //Calculate m and b for: y = m*x + b
        var m = (totalValues*sumXY - sumX*sumY) / (totalValues*sumXX - sumX*sumX);
        var b = (sumY/totalValues) - (m*sumX)/totalValues;

        var lsfLine = [];

        for(var i=0; i < totalValues; i++){
            x = valuesX[i];
            y = x*m + b;
            lsfLine.push([x, y]);
        }

        return lsfLine;
    },
    getCompareRevisionHtml: function(compareRevisionStr, seriesIndex, datapoint){

        var aEl = MS_PAGE.getHgUrlATag('rev', compareRevisionStr);

        if(compareRevisionStr){

            if( !isNaN(seriesIndex) && !isNaN(datapoint) ){

                $(aEl).hover(
                    _.bind(function(){
                        this.plot.highlight(seriesIndex, datapoint);
                    }, this),

                    _.bind(function(){
                        this.plot.unhighlight(seriesIndex, datapoint);
                    }, this)
                    );
            }
        }

        return aEl;
    },
    _handlePushAroundInput: function(event){

        if(event.keyCode === 13){
            if(this.getPushState === false){
                this.getPushes();
            }
        } else {
            //Prevent user from entering anything other than an integer
            var v = $(event.target).val();
            var integersEntered = parseInt(v);
            $(event.target).val(integersEntered || "");
        }
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
    _selectPlot: function(event, ranges){

        var begin = Math.ceil(ranges.xaxis.from);
        var end = parseInt(ranges.xaxis.to);

        var keys = _.keys(this.trendLines);
        var rangeBegin = this.trendLines[keys[0]]['data'][begin]['revisions'][0]['revision'];
        var rangeEnd = this.trendLines[keys[0]]['data'][end]['revisions'][0]['revision'];

        //Retrieve the url for the get range href
        var url = this.model.getPushRangeUrl(rangeBegin, rangeEnd);

        //Set the inputs and href
        this.view.setPushRange(rangeBegin, rangeEnd, url);

    },
    _hoverPlot: function(event, pos, item, noHighlight){

        if(item){

            //Check if the datum display is locked
            var checked = $(this.view.datumLockSel).attr('checked');
            if(checked){
                //Datum locked, do nothing
                return;
            }

            //Highlight the datapoint that the datum info is initialized to
            //ignore if caller specifies noHighlight
            if(!noHighlight){
                this.plot.unhighlight();
                this.plot.highlight(item.seriesIndex, item.datapoint);
            }

            if(item.dataIndex === undefined){
                //dataIndex must be defined to proceed
                return;
            }

            var key = this.seriesIndexToKey[item.seriesIndex][item.dataIndex];

            if(key != this.hoverLegendKey){
                var lastKey = this.hoverLegendKey || key;
                //User has hovered directly from a point on series "a"
                //to a point on series "b", we need to set the point on
                //series "a" back to the appropriate background color
                if(this.trendLines[lastKey] != undefined){
                    this.view.unhighlightLegend(
                        this.trendLines[lastKey].rgb_alpha,
                        this.hoverLegendEl
                        );
                }
            }

            this.hoverLegendKey = key;

            var datum = this.trendLines[key]['data'][ item.datapoint[0] ];
            var dataSeries = this.trendLines[key];

            var platform = this.trendLines[key]['platform'];
            var pagename = this.trendLines[key]['pagename'];

            var id = this.view.getSeriesId(key);
            var legendEl = $('#' + id);

            this.hoverLegendEl = legendEl;

            this.view.highlightLegend(legendEl);

            var metricKeys = [
                'test_evaluation', 'mean', 'trend_mean', 'stddev',
                'trend_stddev', 'p', 'fdr', 'h0_rejected', 'n_replicates' ];

            //If the dz_revision is not defined, data metrics datum has not
            //been received in datazilla, use the first revision associated
            //with the push.
            var revision = datum.dz_revision || datum.revisions[0]['revision'];
            var revisionHtml = MS_PAGE.getHgUrlATag('rev', revision);

            //Configure key/values for the top datum panel holding metrics
            //data
            var keyValueArray = [];

            keyValueArray.push(
                {'label':'dz_revision',
                 'value':revisionHtml });

            keyValueArray.push(
                {'label':'author',
                 'value':datum.user});

            keyValueArray.push(
                {'label':'date',
                 'value':this.view.convertTimestampToDate(datum.date, true)});

            keyValueArray.push(
                {'label':'branch',
                 'value':datum.branch_name});

            keyValueArray.push(
                {'label':'test suite',
                 'value':dataSeries.testsuite});

            keyValueArray.push(
                {'label':'page',
                 'value':pagename});


            //Set the color to use for the datum display panel.
            var color = MS_PAGE.passColor;
            if(datum.metrics_data.length > 0){

                //Metrics data is available load the 'compared to' revision
                var tr = datum.metrics_data[0]['pages'][pagename]['threshold_revision'];

                var revIndex = undefined;

                if( this.revisionToPlotIndex[tr] ){
                    revIndex = this.revisionToPlotIndex[tr];
                }

                var a = this.getCompareRevisionHtml(
                    tr, item.seriesIndex, revIndex
                    );

                keyValueArray.push(
                    {'label':'compared to',
                     'value':a });

                //Load metrics specific data
                for(var i=0; i<metricKeys.length; i++){

                    var mk = metricKeys[i];
                    keyValueArray.push(
                        {'label':mk.replace('_', ' '),
                        'value':datum.metrics_data[0]['pages'][pagename][mk] });
                }

                if( datum.metrics_data[0]['pages'][pagename]['test_evaluation'] === false ){
                    //Test fails, use the fail color
                    color = MS_PAGE.failColor;
                }

            } else {
                //No metrics data use the trendLineColor
                color = this.view.trendLineColor;
            }

            //Set the key/value pairs for the push information section
            //of the datum
            var revisionKeyValues = [];
            this._setPushInfoKeyValues(revisionKeyValues, datum);

            var url = this.model.getRawDataUrl(
                this.trendLines[key], datum.revisions[0].revision);

            var rgbAlpha = this.view.hexToRgb(color);

            this.view.loadDatumLabelContainer(
                keyValueArray, revisionKeyValues, url, rgbAlpha, color
                );

        } else {

            if(this.hoverLegendKey && this.hoverLegendEl){

                if(this.trendLines[this.hoverLegendKey] != undefined){
                    this.view.unhighlightLegend(
                        this.trendLines[this.hoverLegendKey].rgb_alpha,
                        this.hoverLegendEl
                        );
                    this.hoverLegendKey = undefined;
                    this.hoverLegendEl = undefined;
                }
            }
        }
    },
    _setPushInfoKeyValues: function(revisionKeyValues, datum){

        for(var i=0; i<datum.revisions.length; i++){

            var revisionDatum = datum.revisions[i];

            var changesetHtml = MS_PAGE.getHgUrlATag(
                'changeset', revisionDatum.revision
                );

            revisionKeyValues.push(
                {'label':'revision',
                 'value':changesetHtml});

            var contactInfo = revisionDatum.author.match(/(.*?)\<(\S+)\>/);

            var email = "";
            var author = "";

            if(contactInfo.length === 3){
                revisionKeyValues.push(
                    {'label':'author',
                     'value':contactInfo[1]});
                revisionKeyValues.push(
                    {'label':'email',
                     'value':contactInfo[2]});

            }else{
                revisionKeyValues.push(
                    {'label':'author',
                     'value':revisionDatum.author});
            }

            var desc = MS_PAGE.addBugzillaATagsToDesc(revisionDatum.desc);

            revisionKeyValues.push(
                {'label':'desc',
                 'value':desc});
        }
    },
    _clickPlot: function(event, pos, item){
        if(item){

            var checked = $(this.view.datumLockSel).attr('checked');

            if(checked){
                $(this.view.datumLockSel).click();
                this._hoverPlot({}, {}, item);
                $(this.view.datumLockSel).click();
            }else{
                $(this.view.datumLockSel).click();
            }
        }
    },
    _loadTrendLineData: function(data, eventData){

        if(data.length > 0){

            var key = MS_PAGE.getDatumKey(eventData);

            var mean = eventData.mean;

            if(this.trendLines[key]){
                mean = this.trendLines[key].mean;
            }

            this.trendLines[key] = {
                'pagename':eventData.pagename,
                'testsuite':eventData.testsuite,
                'platform':eventData.platform,
                'platform_info':eventData.platform_info,
                'data':data,
                'rgb_alpha':"",
                //This is the mean for the revision of interest.  It's
                //used by pushes with no metrics data to place them along
                //side the revision of interest.
                'mean': mean,
                'datapoint_plot_location':{
                    'series_index':0, 'point_index':0
                    }
                };
        }
    }
});
var TrendLineView = new Class({

    Extends:View,

    jQuery:'TrendLineView',

    initialize: function(selector, options){

        this.setOptions(options);

        this.parent(options);

        this.pushlogSpinnerSel = '#su_pushlog_spinner';
        this.pushlogDashboardSel = '#su_pushlog_dashboard';

        this.eventContainerSel = '#su_container';
        this.pushesAroundRevisionSel = '#su_pushes_around_rev';
        this.chartContainerSel = '#su_trendline_plot';
        this.detailContainerOneSel = '#su_graph_detail_container_1';
        this.datumLockSel = '#su_lock_datum';

        this.pushesBeforeSel = '#su_pushes_before';
        this.pushesAfterSel = '#su_pushes_after';
        this.getPushSpinnerSel = '#su_get_pushes_spinner';
        this.trendLineDisplaySel = '#su_trend_line_display';

        this.pushRangeBeginSel = '#su_push_range_begin';
        this.pushRangeEndSel = '#su_push_range_end';

        this.datumRevision = '#su_datum_revision';
        this.datumRawDataAnchor = '#su_raw_data';
        this.detailContainerTwoSel = '#su_graph_detail_container_2';
        this.detailContainerThreeSel = '#su_graph_detail_container_3';
        this.datumControls = '#su_datum_controls';

        this.lightTextClass = 'su-light-text';
        this.datumValueClass = 'su-datum-value';
        this.patchDescriptionClass = 'su-datum-desc-value';

        this.datumDisplayContainers = [
            this.datumRevision, this.datumControls,
            this.detailContainerTwoSel, this.detailContainerThreeSel
            ];

        this.datasetLegendSel = '#su_legend';
        this.datasetTitleName = 'su_dataset_title';
        this.datasetCbContainerName = 'su_dataset_cb';
        this.datasetCloseName = 'su_dataset_close';
        this.legendIdPrefix = 'su_detail_';

        this.closeIconClassName = 'ui-icon-close';

        this.trendLineColor = '#A9A9A9';

        this.displayedSeriesLabel = {};

        this.getPushesSel = '#su_get_pushes';
        $(this.getPushesSel).button();

        this.getPushRangeSel = '#su_get_range';
        $(this.getPushRangeSel).button();

        this.dashboardDisplayed = false;

        //Set the pushes around revision text
        $(this.pushesAroundRevisionSel).text(MS_PAGE.refData.revision);

    },
    displayDashboard: function(){

        if(this.dashboardDisplayed === false){
            $(this.pushlogSpinnerSel).css('display', 'none');
            $(this.pushlogDashboardSel).css('display', 'block');
        }

    },
    setGetPushState: function(){

        $(this.getPushesSel).button({ "disabled": true });
        $(this.getPushSpinnerSel).css('display', 'block');
    },
    unsetGetPushState: function(){

        $(this.getPushesSel).button({ "disabled": false });
        $(this.getPushSpinnerSel).css('display', 'none');

    },
    showNoDataMessage: function(){

        $(this.pushlogSpinnerSel).css('display', 'none');
        $(this.pushlogDashboardSel).css('display', 'none');

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
        //the hover style.  Setting it dynamically with jquery here.
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
    loadDatumLabelContainer: function(
        datumKeyValues, revisionKeyValues, url, rgbAlpha, color
        ){

        $(this.detailContainerTwoSel).empty();
        $(this.detailContainerThreeSel).empty();

        $(this.datumRawDataAnchor).attr('href', url);
        $(this.datumRawDataAnchor).button();

        for(var i=0; i<this.datumDisplayContainers.length; i++){
            var sel = this.datumDisplayContainers[i];
            $(sel).css('background-color', rgbAlpha);
            $(sel).css('border-color', color);
        }

        this.setDatumKeyValues(
            datumKeyValues, this.detailContainerTwoSel
            );

        this.setDatumKeyValues(
            revisionKeyValues, this.detailContainerThreeSel
            );

    },
    setDatumKeyValues: function(datumKeyValues, container){

        var containerWidth = $(container).css('width');

        for(var i=0; i<datumKeyValues.length; i++){

            var datum = datumKeyValues[i];
            var label = datum['label'];
            var value = datum['value'];

            if(label === 'dz_revision'){
                //This is the revision in the push that's found in
                //datazilla.  Set the datum revision to it.
                $(this.datumRevision).html(value);
                continue;
            }

            var dataDiv = $(document.createElement('div'));
            $(dataDiv).css('width', containerWidth);

            if(label === 'desc'){
                //The revision description fields can be really large
                //make the text lighter to give some visual distinction
                $(dataDiv).addClass(this.lightTextClass);
                $(dataDiv).addClass(this.patchDescriptionClass);
                $(dataDiv).html(value);
                $(container).append(dataDiv);
                continue;
            }

            //Create/set the label span
            var labelSpan = $(document.createElement('span'));

            $(labelSpan).css('text-align', 'left');
            $(labelSpan).addClass(this.lightTextClass);


            $(labelSpan).text(label);
            $(dataDiv).append(labelSpan);

            //Create/set the value span
            var valueSpan = $(document.createElement('span'));

            $(valueSpan).addClass(this.datumValueClass);

            if((label === 'revision') || (label === 'compared to')){
                $(valueSpan).html(value);
            }else{
                $(valueSpan).text(value);
            }
            $(dataDiv).append(valueSpan);

            //Load the data div into the container
            $(container).append(dataDiv);
        }
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
    closeDataSeries: function(key){

        $('#' + this.legendIdPrefix + key).remove();
        delete(this.displayedSeriesLabel[key]);
    },
    setPushCounts: function(pushesBefore, pushesAfter){

        $(this.pushesBeforeSel).val(pushesBefore);
        $(this.pushesAfterSel).val(pushesAfter);

    },
    setPushRange: function(rangeBegin, rangeEnd, url){

        $(this.pushRangeBeginSel).val(rangeBegin);
        $(this.pushRangeEndSel).val(rangeEnd);
        $(this.getPushRangeSel).attr('href', url);

    },
    getPushCounts: function(){

        var counts = {};
        counts.before = $(this.pushesBeforeSel).val();
        counts.after = $(this.pushesAfterSel).val();
        return counts;
    }

});

var TrendLineModel = new Class({

    Extends:Model,

    jQuery:'TrendLineModel',

    initialize: function(options){

        this.setOptions(options);

        this.parent(options);

        this.pushlogUrl = '/' + MS_PAGE.refData.project +
            '/testdata/metrics/' + MS_PAGE.refData.branch + '/' +
            MS_PAGE.refData.revision + '/pushlog';

        this.rawDataUrl = '/' + MS_PAGE.refData.project +
            '/testdata/raw/' + MS_PAGE.refData.branch + '/';

        this.pushRangeUrl = "https://hg.mozilla.org/URI/pushloghtml?" +
            "fromchange=BEGIN&tochange=END";

    },
    getTrendLine: function(
        context, fnSuccess, eventData, pushesBefore, pushesAfter
        ){

        var url = this.getMetricsUrl(eventData, pushesBefore, pushesAfter);

        jQuery.ajax( url, {
            accepts:'application/json',
            dataType:'json',
            cache:false,
            type:'GET',
            context:context,
            success: function(data, textStatus, jqXHR){
                fnSuccess.call(this, data, jqXHR, eventData);
                }
        });
    },
    getMetricsUrl: function(data, pushesBefore, pushesAfter){

        var url = this.getUri(data, this.pushlogUrl);

        url += '&pushes_before=' + pushesBefore;
        url += '&pushes_after=' + pushesAfter;

        return url;
    },
    getRawDataUrl: function(data, revision){

        var url = this.getUri(data, this.rawDataUrl + revision);

        return url;

    },
    getUri: function(data, url){

        url += '?product=' + encodeURIComponent(MS_PAGE.refData.product);
        url += '&branch_version=' + encodeURIComponent(MS_PAGE.refData.branch_version);
        url += '&os_name=' + encodeURIComponent(data.platform_info.operating_system_name);
        url += '&os_version=' + encodeURIComponent(data.platform_info.operating_system_version);
        url += '&processor=' + encodeURIComponent(data.platform_info.processor);
        url += '&build_type=' + encodeURIComponent(data.platform_info.type);
        url += '&test_name=' + encodeURIComponent(data.testsuite);
        url += '&page_name=' + encodeURIComponent(data.pagename);

        return url;
    },
    getPushRangeUrl: function(rangeBegin, rangeEnd){

        var url = this.pushRangeUrl.replace(
            'URI', MS_PAGE.refData.branch_uri
            );
        url = url.replace('BEGIN', rangeBegin);
        url = url.replace('END', rangeEnd);
        return url;

    }

});
