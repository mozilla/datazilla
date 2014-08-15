/*******
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this file,
 * You can obtain one at http://mozilla.org/MPL/2.0/.
 * *****/
var PerformanceGraphComponent = new Class({

    Extends: Component,

    jQuery:'PerformanceGraphComponent',

    initialize: function(selector, options){

        this.setOptions(options);

        this.parent(options);

        this.view = new PerformanceGraphView();
        this.model = new PerformanceGraphModel();

        this.model.getTestTargets( this, this.loadTargets );

        this.appToggleEvent = 'APP_TOGGLE_EV';
        this.testToggleEvent = 'TEST_TOGGLE_EV';
        this.perfPlotClickEvent = 'PERF_PLOT_CLICK_EV';

        this.testData = {};
        this.appData = {}
        this.chartData = {};
        this.seriesIndexDataMap = {};
        this.tickDisplayDates = {};
        this.rangeMap = [];
        this.checkedApps = {};
        this.data = {};

        //Performance targets for different device/test combinations
        this.targets = {};

        this.panFactor = 50;
        this.zoomFactor = 1.5;

        this.goodRev = '';
        this.badRev = '';

        //Caches arguments for _clickPlot for each selected datapoint
        //for handling stateChange
        this.datapointCache = {};

        this.replicatesInitialized = false;
        this.testToggled = false;

        //Set average/median and error-bar from url params
        if(APPS_PAGE.defaults['plot'] != undefined) {
            $(this.view.plotMedianSel).prop(
                'checked', APPS_PAGE.defaults['plot'] == 'median');
        }
        if(APPS_PAGE.defaults['err_bars'] != undefined) {
            $(this.view.plotErrorBarsSel).prop('checked', true);
        }


        this.dialog = $(this.view.rangeB2GHaystackDialog).dialog({

            autoOpen: false,
            height: 575,
            width: 400,
            modal: true,

            buttons: {
                "Reset Fields": _.bind(this.resetDialog, this),
                "Regenerate B2GHaystack": _.bind(this.generateHaystack, this),
            }
        });

        $(APPS_PAGE.appContainerSel).bind(
            this.appToggleEvent, _.bind( this.appToggle, this )
            );

        $(APPS_PAGE.appContainerSel).bind(
            this.testToggleEvent, _.bind( this.testToggle, this )
            );

        $(this.view.chartContainerSel).bind(
            'plotclick', _.bind(this._clickPlot, this)
            );

        $(this.view.chartContainerSel).bind(
            'plothover', _.bind(this._hoverPlot, this)
            );

        $(this.view.chartContainerSel).bind(
            'plotselected', _.bind(this._selectPlot, this)
            );

        $(this.view.timeRangeSel).bind(
            'change', _.bind(this.changeTimeRange, this)
            );

        $(this.view.branchSel).bind(
            'change', _.bind(this.changeTimeRange, this)
            );

        $(this.view.deviceSel).bind(
            'change', _.bind(this.changeTimeRange, this)
            );

        $(this.view.plotAvgSel).bind(
            'change', _.bind(this.refreshPlot, this)
            );

        $(this.view.plotMedianSel).bind(
            'change', _.bind(this.refreshPlot, this)
            );

        $(this.view.plotErrorBarsSel).bind(
            'change', _.bind(this.refreshPlot, this)
            );

        $(this.view.plotZoomInSel).bind(
            'click', _.bind(this.zoomIn, this)
            );

        $(this.view.plotZoomOutSel).bind(
            'click', _.bind(this.zoomOut, this)
            );
        $(this.view.plotPanNorthSel).bind(
            'click', _.bind(this.panUp, this)
            );
        $(this.view.plotPanSouthSel).bind(
            'click', _.bind(this.panDown, this)
            );
        $(this.view.plotPanEastSel).bind(
            'click', _.bind(this.panLeft, this)
            );
        $(this.view.plotPanWestSel).bind(
            'click', _.bind(this.panRight, this)
            );
        $(this.view.plotResetSel).bind(
            'click', _.bind(this.refreshPlot, this)
            );
        $(this.view.plotNavControlsSel).bind(
            'click', _.bind(this.displayNavMenu, this)
            );

        $(APPS_PAGE.appContainerSel).bind(
            APPS_PAGE.stateChangeEvent,
            _.bind(this.stateChange, this)
            );
    },
    getChartOptions: function(){

        var chartOptions = {
            'grid': {
                'clickable': true,
                'hoverable': true,
                'autoHighlight': true,
                'color': '#B6B6B6',
                'borderWidth': 0.5,

            },

            'xaxis': {
                'tickFormatter': _.bind(this.formatLabel, this)
            },

            'yaxis': {
                'autoscaleMargin':0.3
            },
            'series': {

                'points': {
                    'radius': 2.5,
                    'errorbars': 'y',
                    'yerr': {
                         'show': true,
                         'upperCap':'-',
                         'lowerCap':'-',
                         'color': '#CCCCCC'
                        }
                }
            },

            'selection':{
                'mode':'x',
                'color':'#BDBDBD'
            }
        };

        return chartOptions;
    },
    loadTargets: function(data){

        this.targets = data.data;
    },
    setMarkings: function(chartOptions){

        var device = $(this.view.deviceSel).val() || APPS_PAGE.defaults['device'];
        var testName = this.testData.url.replace(/_/g, ' ');

        var targetMarkings = {
            'markings': [
                { 'color': '#b0cdcb',
                  'lineWidth': 4,
                  'label': 'Performance target',
                  'yaxis': { 'from': 0, 'to': 0 },
                },
            ]
        };

        if( this.targets[device] != undefined ){
            var test;
            for(test in this.targets[device] ){
                if( test.indexOf( testName ) > -1 ){

                    targetMarkings['markings'][0]['yaxis']['from'] = this.targets[device][test];
                    targetMarkings['markings'][0]['yaxis']['to'] = this.targets[device][test];

                    _.extend(chartOptions.grid, targetMarkings);

                    break;
                }
            }
        }
    },
    displayNavMenu: function(event){

        var visible = $(this.view.plotControlMenuSel).is(":visible");

        if(visible){
            $(this.view.plotControlMenuSel).hide();
        }else {
            $(this.view.plotControlMenuSel).show();
        }

    },
    zoomOut: function(event){
        var axes = this.plot.getAxes();
        var xaxis = axes.xaxis;
        var yaxis = axes.yaxis;
        var center = this.plot.p2c({ x: (xaxis.min + xaxis.max) / 2, y: (yaxis.min + yaxis.max) / 2 });
        this.plot.zoom({ amount: this.zoomFactor, center: center });
        this.plot.triggerRedrawOverlay();
    },
    zoomIn: function(event){

        var axes = this.plot.getAxes();
        var xaxis = axes.xaxis;
        var yaxis = axes.yaxis;
        var center = this.plot.p2c({ x: (xaxis.min + xaxis.max) / 2, y: (yaxis.min + yaxis.max) / 2 });
        this.plot.zoomOut({ amount: this.zoomFactor, center: center });

        this.plot.triggerRedrawOverlay();
    },
    panDown: function(){
        this.plot.pan({ top: this.panFactor });
        this.plot.triggerRedrawOverlay();
    },
    panRight: function(){
        this.plot.pan({ left: -this.panFactor });
        this.plot.triggerRedrawOverlay();
    },
    panUp: function(){
        this.plot.pan({ top: -this.panFactor });
        this.plot.triggerRedrawOverlay();
    },
    panLeft: function(){
        this.plot.pan({ left: this.panFactor });
        this.plot.triggerRedrawOverlay();
    },
    _selectPlot: function(event, ranges, x){


        var from = Math.round(ranges.xaxis.from);
        var to = Math.round(ranges.xaxis.to);

        var fromData = this.rangeMap[from];
        var toData = this.rangeMap[to];

        this.goodRev = fromData;
        this.badRev = toData;

        var plotControls = this.view.getPlotControlVals();

        if(plotControls.avg){
            if(fromData.avg > toData.avg){
                this.goodRev = toData;
                this.badRev = fromData;
            }
        } else if (plotControls.median){
            if(fromData.median > toData.median){
                this.goodRev = toData;
                this.badRev = fromData;
            }
        }

        if(!_.isEmpty(fromData) && !_.isEmpty(toData)){

            this.view.setDialogData(
                this.goodRev, this.badRev, this.checkedApps);
            //Open Modal Window
            this.dialog.dialog('open');
        }
    },
    resetDialog: function(){

        this.view.setDialogData(
            this.goodRev, this.badRev, this.checkedApps);

    },
    generateHaystack: function(){

        this.view.generateB2GHaystackCmd();

    },
    formatLabel: function(label, series){
        return this.tickDisplayDates[label] || "";
    },
    changeTimeRange: function(event){
        this.testToggle(event, this.testData);
    },
    appToggle: function(event, data){

        if(this.checkedApps[ data['test_id'] ]){

            this.checkedApps[ data['test_id'] ] = false;

        }else{

            this.checkedApps[ data['test_id'] ] = true;

        }

        if(!_.isEmpty(this.data)){
            this.renderPlot(this.data);
        }

    },
    testToggle: function(event, data){

        this.testData = data;

        this.view.setGraphTestName(this.testData.url);

        var testIds = _.keys(data.test_ids);

        var range = $(this.view.timeRangeSel).val();
        var branch = $(this.view.branchSel).val();
        var device = $(this.view.deviceSel).val() || APPS_PAGE.defaults['device'];

        this.view.hideData();

        this.testToggled = true;

        this.model.getAppData(
            this, this.renderPlot, testIds.join(','), data.url, range,
            branch, device
            );
    },
    refreshPlot: function(event){
        this.renderPlot(this.data);
    },
    renderPlot: function(data){

        this.data = data;

        this.chartData = {};
        this.tickDisplayDates = {};

        var testId = 0;
        var appColor = "";
        var appName = "";
        var timestamp = "";
        var formattedTime = "";
        var dataLength = data.length;
        var appNames = {};

        var controlValues = this.view.getPlotControlVals();

        this.view.setGraphType(controlValues);

        var i = 0;
        for(; i<dataLength; i++){

            testId = data[i]['test_id'];

            appName = this.testData['test_ids'][testId]['name'];

            if((appName == undefined) ||
                (APPS_PAGE.excludeList[appName] != undefined)){
                continue;
            }

            appColor = this.testData['test_ids'][testId]['color'];

            //appNames to display
            appNames[appName] = true;

            if(!this.chartData[ testId ]){
                this.chartData[ testId ] = {};
                this.chartData[ testId ][ 'id' ] = testId;
                this.chartData[ testId ][ 'name' ] = appName;
                this.chartData[ testId ][ 'color' ] = appColor;
                this.chartData[ testId ][ 'background_color' ] = this.view.hexToRgb(appColor);
                this.chartData[ testId ][ 'points' ] = { 'show': true };
                this.chartData[ testId ][ 'lines' ] = { 'show': true };
                this.chartData[ testId ][ 'data' ] = [];
                this.chartData[ testId ][ 'full_data' ] = [];

            }

            timestamp = data[i]['date_run'];

            //Don't add x-axis labels to the first and last x-axis values
            if((i > 0) && (i < dataLength - 1)){
                formattedTime = this.view.convertTimestampToDate(timestamp);
                this.tickDisplayDates[ i ] = formattedTime;
            }

            if(!data[i]['formatted_date_run']){
                data[i]['formatted_date_run'] = this.view.convertTimestampToDate(
                    timestamp, true
                    );
            }

            //Data for flot
            if(controlValues.median === true){
                this.chartData[ testId ][ 'data' ].push(
                    [ i, data[i]['median'], data[i]['std'] ]
                    );
            }else {
                this.chartData[ testId ][ 'data' ].push(
                    [ i, data[i]['avg'], data[i]['std'] ]
                    );

            }

            //Data for presentation
            this.chartData[ testId ][ 'full_data' ].push(
                [ data[i] ]
                );

            if(_.isEmpty( this.rangeMap[i] )){
                this.rangeMap[i] = {
                    build_revision:data[i].build_revision,
                    gecko_revision:data[i].gecko_revision,
                    gaia_revision:data[i].revision,
                    device:data[i].type,
                    avg:data[i].avg,
                    mean:data[i].mean
                }
            }
        }

        var chart = [];
        var testIds = _.keys(this.chartData);

        var j = 0;
        var seriesIndex = 0;
        var defaultAppName = APPS_PAGE.defaults['app'];
        var dsIndex = 0;

        this.seriesIndexDataMap = {};

        for(j = 0; j<testIds.length; j++){

            if(this.checkedApps && !this.checkedApps[ testIds[j] ]){
                continue;
            }

            seriesIndex = chart.push( this.chartData[ testIds[j] ] ) - 1
            this.seriesIndexDataMap[seriesIndex] = this.chartData[ testIds[j] ];

            //Set default app name
            if(this.chartData[ testIds[j] ].name === defaultAppName){
                dsIndex = seriesIndex;
            }
        }

        //Only display app names that are found in the dataset
        APPS_PAGE.graphControlsComponent.displayApps(appNames, this.testToggled);

        this.view.showData(_.isEmpty(this.data));

        var chartOptions = this.getChartOptions();

        if(controlValues.error_bars === false){
            chartOptions.series.points.errorbars = 'n';
        }else{
            chartOptions.series.points.errorbars = 'y';
        }

        this.setMarkings(chartOptions);

        this.plot = $.plot(
            $(this.view.chartContainerSel),
            chart,
            chartOptions
            );

        if(!this.replicatesInitialized && this.seriesIndexDataMap[seriesIndex]){

            var dpIndex = this.seriesIndexDataMap[dsIndex]['data'].length - 1;

            var gaiaRev = APPS_PAGE.defaults['gaia_rev'];
            var geckoRev = APPS_PAGE.defaults['gecko_rev'];
            var k = 0;

            //Set defaulDataIndex to what was specified in the url params
            if( (gaiaRev != undefined) && (geckoRev != undefined) ){
                for(k=0; k<this.seriesIndexDataMap[dsIndex]['full_data'].length; k++){
                    var defaultDatum = this.seriesIndexDataMap[dsIndex]['full_data'][k][0];
                    if( (defaultDatum.revision.indexOf( gaiaRev ) > -1) &&
                        (defaultDatum.gecko_revision.indexOf( geckoRev ) > -1 )){
                        dpIndex = k;
                        break;
                    }
                }
            }

            //Simulate plot click on first series, last datapoint
            this._clickPlot(
                {}, {}, {'seriesIndex':dsIndex, 'dataIndex':dpIndex}
                );

            this.view.resetSeriesLabelBackground(this.chartData);
            this.replicatesInitialized = true;

        }else {
            APPS_PAGE.saveState();
        }

    },
    stateChange: function(event, data){

        if(data['branch'] != undefined) {

            this.view.selectOption(data['branch'], this.view.branchSel);

        }else if(data['range'] != undefined){

            this.view.selectOption(data['range'], this.view.timeRangeSel);

        }else if( (data['app'] != undefined) ||
                  (data['gaia_rev'] != undefined) ||
                  (data['gecko_rev'] != undefined)  ){

            var args = this.datapointCache[ data['datapoint_hash'] ];
            this._clickPlot(args['ev'], args['pos'], args['item']);
        }
    },
    _clickPlot: function(event, pos, item){

        if(item != null){
            var seriesDatum = this.seriesIndexDataMap[ item.seriesIndex ];
            var datapointDatum = this.seriesIndexDataMap[ item.seriesIndex ]['full_data'][ item.dataIndex ];

            var keyHash = APPS_PAGE.getDatapointHashCode(
                seriesDatum.name, datapointDatum[0].revision,
                datapointDatum[0].gecko_revision
                );

            this.datapointCache[keyHash] = {
                'ev':event, 'pos':pos, 'item':item
                };

            this.plot.unhighlight();

            this.plot.highlight(item.seriesIndex, item.dataIndex);

            this._hoverPlot(event, pos, item);

            datapointDatum[0]['branch'] = $(this.view.branchSel).val();

            $(APPS_PAGE.appContainerSel).trigger(
                this.perfPlotClickEvent,
                { 'seriesIndex':item.seriesIndex,
                  'dataIndex':item.dataIndex,
                  'series':seriesDatum,
                  'datapoint':datapointDatum[0] }
                );
        }
    },
    _hoverPlot: function(event, pos, item){

        this.view.resetSeriesLabelBackground(this.chartData);

        if(item != null){
            var seriesDatum = this.seriesIndexDataMap[ item.seriesIndex ];
            var datapointDatum = this.seriesIndexDataMap[ item.seriesIndex ]['full_data'][ item.dataIndex ];
            this.view.setDetailContainer(seriesDatum, datapointDatum[0]);
            this.view.highlightSeriesLabel(seriesDatum);
        }
    }
});
var PerformanceGraphView = new Class({

    Extends:View,

    jQuery:'PerformanceGraphView',

    initialize: function(selector, options){

        this.setOptions(options);

        this.parent(options);

        this.timeRangeSel = '#app_time_range';
        this.branchSel = '#app_branch';
        this.deviceSel = '#app_device';
        this.chartContainerSel = '#app_perf_chart';
        this.noChartDataMessageSel = '#app_perf_no_chartdata';
        this.appTestName = '#app_test_name';
        this.graphDetailContainerSel = '#app_perf_detail_container';
        this.perfDataContainerSel = '#app_perf_data_container';
        this.perfWaitSel = '#app_perf_wait';

        this.testNameSpanSel = '#app_replicate_test';
        this.appNameSpanSel = '#app_replicate_application';
        this.gaiaRevisionSel = '#app_replicate_revision';
        this.geckoRevisionSel = '#app_replicate_gecko_revision';
        this.appSeriesSel = '#app_series';
        this.testSeriesSel = '#test_series';

        this.plotAvgSel = '#app_plot_avg';
        this.plotMedianSel = '#app_plot_median';
        this.plotErrorBarsSel = '#app_plot_error_bars';

        this.plotNavControlsSel = '#app_control_menu';
        this.plotControlMenuSel = '#app_navigation_menu_body';
        this.plotZoomInSel = '#app_zoom_in';
        this.plotZoomOutSel = '#app_zoom_out';
        this.plotPanNorthSel = '#app_pan_n';
        this.plotPanSouthSel = '#app_pan_s';
        this.plotPanEastSel = '#app_pan_e';
        this.plotPanWestSel = '#app_pan_w';
        this.plotResetSel = '#app_pan_home';

        this.plotPerformanceTypeClsSel = '.app-y-axis-type';

        this.detailIdPrefix = 'app_series_';
        this.idFields = [
            'revision', 'formatted_date_run', 'avg', 'median', 'std', 'min', 'max'
            ];
        this.appDetailIdSel = '#' + this.detailIdPrefix + 'application';

        this.appSeriesIdPrefix = 'app_series_';

        this.rangeB2GHaystackDialog = '#app_b2ghaystack_dialog';


    },
    setDialogData: function(goodRev, badRev, checkedApps){

        $('[name="device_name"]').val(goodRev.device);
        $('[name="job_name"]').val(APPS_PAGE.defaults['test']);
        $('[name="good_rev"]').val(goodRev.gaia_revision);
        $('[name="bad_rev"]').val(badRev.gaia_revision);

        var selectedAppNames = [];
        var appName = "";
        for(var id in checkedApps){
            if(checkedApps[id] === true){
                appName = APPS_PAGE.graphControlsComponent.appLookup[id].name;
                if(appName === 'email FTU'){
                    appName = 'email';
                }
                selectedAppNames.push(appName);
            }
        }
        $('[name="applications"]').val(selectedAppNames.join(' '));

        this.generateB2GHaystackCmd();
    },
    generateB2GHaystackCmd: function(){

        var optionalArgs = ['applications', 'max_builds', 'branch', 'jenkins_url'];
        var positionalArgs = ['device_name', 'job_name', 'good_rev', 'bad_rev'];

        var cmd = "b2ghaystack ";

        for(var i=0; i<optionalArgs.length; i++){

            var optionValue = $('[for="' + optionalArgs[i] + '"]').text();
            var argValue = $('[name="' + optionalArgs[i] + '"]').val();

            cmd += optionValue + ' ' + argValue + ' ';
        }
        for(var i=0; i<positionalArgs.length; i++){
            var argValue = $('[name="' + positionalArgs[i] + '"]').val();
            cmd += ' ' + argValue;
        }

        var textareaEl = $('[name="b2g_haystack_cmd"]');
        $(textareaEl).val(cmd);

    },
    showData: function(noData){

        $(this.perfWaitSel).css('display', 'none');

        if(noData){

            $(this.perfDataContainerSel).css('display', 'none');
            $(this.chartContainerSel).css('display', 'none');
            $(this.noChartDataMessageSel).css('display', 'block');

            APPS_PAGE.replicateGaphComponent.view.showData(noData);

        }else{

            $(this.noChartDataMessageSel).css('display', 'none');
            $(this.chartContainerSel).css('display', 'block');

        }

        $(this.perfDataContainerSel).css('display', 'block');
    },
    hideData: function(){
        $(this.perfDataContainerSel).css('display', 'none');
        $(this.perfWaitSel).css('display', 'block');
    },
    highlightSeriesLabel: function(seriesDatum){
        $('#' + this.appSeriesIdPrefix + seriesDatum.id ).css(
            'background-color', 'white'
            );
    },
    resetSeriesLabelBackground: function(chartData){
        var testId = 0;
        for(testId in chartData){
            $('#' + this.appSeriesIdPrefix + testId ).css(
                'background-color', chartData[ testId ][ 'background_color' ]
                );
        }
    },
    setGraphTestName: function(name){

        var max = 20;
        var displayName = name;

        if(displayName.length > max){
            displayName = displayName.substr(0, max-1) + '...';
        }

        $(this.appTestName).text(displayName);
        $(this.appTestName).attr('title', name);
    },
    setDetailContainer: function(seriesDatum, datapointDatum){

        $(this.graphDetailContainerSel).css(
            'background-color', seriesDatum.background_color
            );
        $(this.graphDetailContainerSel).css(
            'border-color', seriesDatum.color
            );
        $(this.graphDetailContainerSel).css(
            'border-width', 1
            );

        $(this.appDetailIdSel).text( seriesDatum['name'] );
        var i = 0;
        var fieldName = "";
        var idSel = "";
        var value = "";

        for(i = 0; i<this.idFields.length; i++){
            fieldName = this.idFields[i];
            idSel = '#' + this.detailIdPrefix + fieldName;

            value = datapointDatum[fieldName];

            if(fieldName === 'revision'){
                value = APPS_PAGE.getRevisionSlice(
                    datapointDatum[fieldName]
                    );
                $(idSel).attr('title', datapointDatum[fieldName]);
                $(idSel).attr('href', APPS_PAGE.gaiaHrefBase + value);
            }

            $(idSel).text( value );
        }
    },
    selectOption: function(val, target){

        //Unselect whatever is selected
        var currentSelectedVal = $(target).find(":selected");
        $(currentSelectedVal).attr('selected', '');

        //Get the option that corresponds to the value
        var optionEl = $(target).find('[value="' + val + '"]');

        //Select the matching option
        $(optionEl).attr("selected", "selected");

        //fire the change event
        $(target).change();
    },
    getPlotControlVals: function(){
        return {
            'avg': $(this.plotAvgSel).is(':checked'),
            'median': $(this.plotMedianSel).is(':checked'),
            'error_bars': $(this.plotErrorBarsSel).is(':checked')
            }
    },
    setGraphType: function(controlVals){
        if( controlVals.median ){
            $(this.plotPerformanceTypeClsSel).text('Median');
        }else {
            $(this.plotPerformanceTypeClsSel).text('Average');
        }
    }
});
var PerformanceGraphModel = new Class({

    Extends:Model,

    jQuery:'PerformanceGraphModel',

    initialize: function(options){

        this.setOptions(options);

        this.parent(options);

    },

    getTestTargets: function(context, fnSuccess){

        var url = APPS_PAGE.urlBase + 'refdata/perftest/testtargets';
        jQuery.ajax( url, {
            accepts:'application/json',
            dataType:'json',
            cache:false,
            type:'GET',
            data:data,
            context:context,
            success:fnSuccess,
        });
    },
    getAppData: function(
        context, fnSuccess, testIds, pageName, range, branch, device){

        var uri = APPS_PAGE.urlBase + 'testdata/test_values?' +
            'branch=BRANCH&test_ids=TEST_IDS&page_name=PAGE_NAME&' +
            'range=RANGE&device=DEVICE';

        uri = uri.replace('BRANCH', branch);
        uri = uri.replace('TEST_IDS', testIds);
        uri = uri.replace('PAGE_NAME', pageName);
        uri = uri.replace('RANGE', range);
        uri = uri.replace('DEVICE', device);

        jQuery.ajax( uri, {
            accepts:'application/json',
            dataType:'json',
            cache:false,
            type:'GET',
            data:data,
            context:context,
            success:fnSuccess,
        });
    }
});
