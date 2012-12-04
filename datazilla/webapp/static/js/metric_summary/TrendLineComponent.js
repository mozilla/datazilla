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

        //Holds all event data received. It's used for
        //reloading all series data with updated pushes
        //before and after values.
        this.eventData = [];

        this.pushesBefore = 20;
        this.pushesAfter = 5;

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
                'autoscaleMargin':0.1
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

        //Set the push counts in the HTML
        this.view.setPushCounts(this.pushesBefore, this.pushesAfter);

        //Simulate click on the default test suite table row
        $(this.view.eventContainerSel).bind(
            this.defaultRowSelectionEvent,
            _.bind(this.clickTableCB, this)
            );

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
                this, this.loadTrendData, this.dataLoadError, eventData,
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
                this, this.loadTrendData, this.dataLoadError,
                trendLineEventData, pushCounts.before, pushCounts.after
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

        chartData.push(passDataset);
        chartData.push(failDataset);
        chartData.push(noDataDataset);

        for(var i=0; i<this.trendLineOrder.length; i++){

            var key = this.trendLineOrder[i];

            var passData = [];
            var failData = [];
            var trendData = [];

            var seriesColor = '';
            var targetRevisionType = 'pass';

            var trendDataset = this.getTrendLineDataset();
            var trendIndex = chartData.push(trendDataset) - 1;

            this.seriesIndexToKey[trendIndex] = [];

            var passIndex = 0;
            var failIndex = 0;
            var noDataIndex = 0;

            var metricsData = [];

            for(var j=0; j<this.trendLines[key]['data'].length; j++){

                metricsData = this.trendLines[key]['data'][j]['metrics_data'];

                //Store x axis tick labels
                if(!this.tickDisplayDates[j]){

                    var tickLabel = "";

                    //Exclude first and last tick labels on the x-axis
                    //to keep things unclutered
                    if((j > 0) && (j <this.trendLines[key]['data'].length - 1)){
                        var unixTimestamp = this.trendLines[key]['data'][j]['date'];
                        tickLabel = this.convertTimestampToDate(
                            unixTimestamp, false
                            );
                    }

                    this.tickDisplayDates[j] = tickLabel;
                }

                if(metricsData.length > 0){
                    var pageData =
                        metricsData[0]['pages'][this.trendLines[key]['pagename'] ];

                    //Metrics data is available set trend datum
                    var trendDatumIndex = chartData[trendIndex].data.push(
                        [ j, parseInt(pageData.trend_mean) ]
                        ) - 1;

                    this.seriesIndexToKey[trendIndex][trendDatumIndex] = key;

                    if( pageData.test_evaluation === true ){

                        //Test passed
                        passIndex = chartData[this.passSeriesIndex].data.push(
                            [ j, parseInt(pageData.mean) ]
                            ) - 1;

                        this.seriesIndexToKey[this.passSeriesIndex][passIndex] = key;

                    } else if(pageData.test_evaluation === false) {

                        //Test failed

                        failIndex = chartData[this.failSeriesIndex].data.push(
                            [ j, parseInt(pageData.mean) ]
                            ) - 1;

                        this.seriesIndexToKey[this.failSeriesIndex][failIndex] = key;

                    }

                    //revision that is loaded in the page
                    if( this.trendLines[key]['data'][j]['dz_revision'] ===
                        MS_PAGE.refData.revision ){

                        targetRevisions.push(
                            {'x':j, 'y':parseInt(pageData.mean) }
                            );

                        flotItem.datapoint = [
                            j, pageData.mean
                            ];

                        if( pageData.test_evaluation === true ){

                            seriesColor = MS_PAGE.passColor;

                            this.trendLines[key].datapoint_plot_location.point_index = passIndex;

                            flotItem.seriesIndex = this.passSeriesIndex;
                            flotItem.dataIndex =
                                this.trendLines[key].datapoint_plot_location.point_index;

                        } else {

                            targetRevisionType = 'fail';

                            seriesColor = MS_PAGE.failColor;

                            this.trendLines[key].datapoint_plot_location.point_index = failIndex;

                            flotItem.seriesIndex = this.failSeriesIndex;
                            flotItem.dataIndex = 
                                this.trendLines[key].datapoint_plot_location.point_index;

                        }
                    }

                } else {
                    //No metrics data is available, color gray and place
                    //on trend line
                    noDataIndex = chartData[this.noMetricsDataSeriesIndex].data.push(
                        [ j, parseInt(this.trendLines[key]['mean']) ]
                        ) - 1;

                    this.seriesIndexToKey[this.noMetricsDataSeriesIndex][noDataIndex] = key;
                }

            }

            if(targetRevisionType === 'pass'){
                this.trendLines[key].datapoint_plot_location.series_index = this.passSeriesIndex;
            }else{
                this.trendLines[key].datapoint_plot_location.series_index = this.failSeriesIndex;
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

        $(window).resize(
            //Redraw the circle around target revision
            //when the chart is resized
            _.bind(
                function(){
                    //this.view.drawCircleAroundDataPoints(
                     //   targetRevisions, this.plot
                      //  );
                }, this)
            );
        this.unsetGetPushState();
        this.view.displayDashboard();

        //Set hover datum to revision of interest
        this._hoverPlot({}, {}, flotItem);

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
    convertTimestampToDate: function(unixTimestamp, getHMS){
        var dateObj = new Date(unixTimestamp * 1000);
        var dateString = dateObj.getFullYear() + '-' +
            this.padNumber((dateObj.getMonth() + 1), 10, '0') + '-' +
            dateObj.getDate();

        if(getHMS){
            dateString += ' ' +
                dateObj.getHours() + ':' +
                dateObj.getMinutes() + ':' +
                this.padNumber(dateObj.getSeconds(), 10, '0');
        }

        return dateString;
    },
    padNumber: function(n, max, pad){

        n = parseInt(n);

        if( n < max ){
            return pad + n;
        }

        return n;
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
        this.loadTrendData([], {});
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

        //Don't care what the series is, just need the data index
        //equivalent
        var keys = _.keys(this.trendLines);
        var rangeBegin = this.trendLines[keys[0]]['data'][begin]['revisions'][0]['revision'];
        var rangeEnd = this.trendLines[keys[0]]['data'][end]['revisions'][0]['revision'];

        //Retrieve the url for the get range href
        var url = this.model.getPushRangeUrl(rangeBegin, rangeEnd);

        //Set the inputs and href
        this.view.setPushRange(rangeBegin, rangeEnd, url);

    },
    _hoverPlot: function(event, pos, item){

        if(item){

            //Check if the datum display is locked
            var checked = $(this.view.datumLockSel).attr('checked');
            if(checked){
                //Datum locked, do nothing
                return;
            }

            //Highlight the datapoint that the datum info is initialized to
            this.plot.unhighlight();

            this.plot.highlight(item.seriesIndex, item.datapoint);

            if(item.dataIndex === undefined){
                //dataIndex must be defined to proceed
                return;
            }

            var key = this.seriesIndexToKey[item.seriesIndex][item.dataIndex];

            if(key != this.hoverLegendKey){
                var lastKey = this.hoverLegendKey || key;
                //User has hovered directly from a point on series a
                //to a point on series b, we need to set the point on
                //series a back to the appropriate background color
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

            var keyValueArray = [];
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

            keyValueArray.push(
                {'label':'dz_revision',
                 'value':revisionHtml });

            keyValueArray.push(
                {'label':'author',
                 'value':datum.user});

            keyValueArray.push(
                {'label':'date',
                 'value':this.convertTimestampToDate(datum.date, true)});

            keyValueArray.push(
                {'label':'branch',
                 'value':datum.branch_name});

            keyValueArray.push(
                {'label':'test suite',
                 'value':dataSeries.testsuite});

            keyValueArray.push(
                {'label':'page',
                 'value':pagename});

            var color = MS_PAGE.passColor;

            if(datum.metrics_data.length > 0){
                //Load metrics specific data
                for(var i=0; i<metricKeys.length; i++){

                    var mk = metricKeys[i];
                    keyValueArray.push(
                        {'label':mk.replace('_', ' '),
                        'value':datum.metrics_data[0]['pages'][pagename][mk] });
                }

                if( datum.metrics_data[0]['pages'][pagename]['test_evaluation'] === false ){
                    color = MS_PAGE.failColor;
                }

            } else {
                color = this.view.trendLineColor;
            }

            var revisionKeyValues = [];
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
    _clickPlot: function(event, pos, item){
        if(item){
            $(this.view.datumLockSel).click();
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


        //Set the pushes around revision
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

            if(label === 'revision'){
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
    hexToRgb: function(hex) {

        var result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);

        //Add alpha channel to lighten the color
        var rgbAlpha = 'rgba(' + parseInt(result[1], 16) + ',' +
            parseInt(result[2], 16) + ',' +
            parseInt(result[3], 16) + ',0.1)';

        return rgbAlpha;
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
        context, fnSuccess, fnError, eventData, pushesBefore, pushesAfter
        ){

        var url = this.getMetricsUrl(eventData, pushesBefore, pushesAfter);

        jQuery.ajax( url, {
            accepts:'application/json',
            dataType:'json',
            cache:false,
            type:'GET',
            context:context,
            error:fnError,
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

        url += '?product=' + MS_PAGE.refData.product;
        url += '&branch_version=' + MS_PAGE.refData.branch_version;
        url += '&os_name=' + data.platform_info.operating_system_name;
        url += '&os_version=' + data.platform_info.operating_system_version;
        url += '&processor=' + data.platform_info.processor;
        url += '&build_type=' + data.platform_info.type;
        url += '&test_name=' + data.testsuite;
        url += '&page_name=' + data.pagename;

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
