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

        this.appToggleEvent = 'APP_TOGGLE_EV';
        this.testToggleEvent = 'TEST_TOGGLE_EV';
        this.perfPlotClickEvent = 'PERF_PLOT_CLICK_EV';

        this.testData = {};
        this.appData = {}
        this.chartData = {};
        this.seriesIndexDataMap = {};
        this.tickDisplayDates = {};
        this.checkedApps = {};
        this.data = {};

        this.replicatesInitialized = false;
        this.testToggled = false;

        this.chartOptions = {
            'grid': {
                'clickable': true,
                'hoverable': true,
                'autoHighlight': true,
                'color': '#B6B6B6',
                'borderWidth': 0.5
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
            }
        };

        $(this.view.appContainerSel).bind(
            this.appToggleEvent, _.bind( this.appToggle, this )
            );

        $(this.view.appContainerSel).bind(
            this.testToggleEvent, _.bind( this.testToggle, this )
            );

        $(this.view.chartContainerSel).bind(
            'plotclick', _.bind(this._clickPlot, this)
            );

        $(this.view.chartContainerSel).bind(
            'plothover', _.bind(this._hoverPlot, this)
            );

        $(this.view.timeRangeSel).bind(
            'change', _.bind(this.changeTimeRange, this)
            );

        $(this.view.branchSel).bind(
            'change', _.bind(this.changeTimeRange, this)
            );
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

        if(!_.isEmpty(this.data) && (this.testToggled === true)){
            this.renderPlot(this.data);
        }

    },
    testToggle: function(event, data){

        this.testData = data;

        this.view.setGraphTestName(this.testData.url);

        var testIds = _.keys(data.test_ids);

        var range = $(this.view.timeRangeSel).val();
        var branch = $(this.view.branchSel).val();

        this.view.hideData();

        this.testToggled = true;

        this.model.getAppData(
            this, this.renderPlot, testIds.join(','), data.url, range,
            branch
            );
    },
    renderPlot: function(data){

        this.data = data;

        this.chartData = {};
        this.tickDisplayDates = {};

        var i = 0;

        var testId = 0;
        var appColor = "";
        var appName = "";
        var timestamp = "";
        var formattedTime = "";
        var dataLength = data.length;
        var appNames = {};


        for(i = 0; i<dataLength; i++){

            testId = data[i]['test_id'];

            appName = this.testData['test_ids'][testId]['name'];
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
            this.chartData[ testId ][ 'data' ].push(
                [ i, data[i]['avg'] ]
                );

            //Data for presentation
            this.chartData[ testId ][ 'full_data' ].push(
                [ data[i] ]
                );
        }

        //Only display app names that are found in the dataset
        APPS_PAGE.graphControlsComponent.displayApps(appNames);

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

        this.view.showData(_.isEmpty(this.data));

        this.plot = $.plot(
            $(this.view.chartContainerSel),
            chart,
            this.chartOptions
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
                {}, {}, { 'seriesIndex':dsIndex, 'dataIndex':dpIndex }
                );

            this.view.resetSeriesLabelBackground(this.chartData);
            this.replicatesInitialized = true;

        }
    },
    _clickPlot: function(event, pos, item){

        if(item != null){
            var seriesDatum = this.seriesIndexDataMap[ item.seriesIndex ];
            var datapointDatum = this.seriesIndexDataMap[ item.seriesIndex ]['full_data'][ item.dataIndex ];

            this.plot.unhighlight();

            this.plot.highlight(item.seriesIndex, item.dataIndex);

            this._hoverPlot(event, pos, item);

            datapointDatum[0]['branch'] = $(this.view.branchSel).val();

            $(this.view.appContainerSel).trigger(
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

        this.appContainerSel = '#app_container';

        this.timeRangeSel = '#app_time_range';
        this.branchSel = '#app_branch';
        this.chartContainerSel = '#app_perf_chart';
        this.noChartDataMessageSel = '#app_perf_no_chartdata';
        this.appTestName = '#app_test_name';
        this.graphDetailContainerSel = '#app_perf_detail_container';
        this.perfDataContainerSel = '#app_perf_data_container';
        this.perfWaitSel = '#app_perf_wait';

        this.permalinkSel = '#app_permalink';
        this.permalinkContainerSel = '#app_link';

        this.testNameSpanSel = '#app_replicate_test';
        this.appNameSpanSel = '#app_replicate_application';
        this.gaiaRevisionSel = '#app_replicate_revision';
        this.geckoRevisionSel = '#app_replicate_gecko_revision';
        this.appSeriesSel = '#app_series';
        this.testSeriesSel = '#test_series';


        this.detailIdPrefix = 'app_series_';
        this.idFields = [
            'revision', 'formatted_date_run', 'avg', 'std', 'min', 'max'
            ];
        this.appDetailIdSel = '#' + this.detailIdPrefix + 'application';

        this.appSeriesIdPrefix = 'app_series_';

        $(this.permalinkSel).bind(
            'click', _.bind(this.setPermalinkHref, this)
            );

        $(document).bind(
            'click', _.bind(this.hidePermalink, this)
            );
    },
    hidePermalink: function(event){

        if(event != undefined){
            var targetId = $(event.target).attr('id');
            var permalinkId = this.permalinkSel.replace('#', '');

            if(targetId != permalinkId){
                $(this.permalinkContainerSel).css('display', 'none');
            }

        }else {
            $(this.permalinkContainerSel).css('display', 'none');
        }
    },
    setPermalinkHref: function(event){

        var display = $(this.permalinkContainerSel).css('display');

        if(display === 'block'){
            this.hidePermalink();
            return;
        }

        var params = [];

        var branch = $(this.branchSel).find(":selected").text();
        params.push('branch=' + branch);

        var range = $(this.timeRangeSel).find(":selected").val();
        params.push('range=' + range);

        var test = $(this.testSeriesSel).find('input:checked').next().text();
        params.push('test=' + test);

        var app = $(this.appNameSpanSel).text();
        params.push('app=' + app);

        var appListEls = $(this.appSeriesSel).find("input:checkbox:checked");
        var appList = [];
        _.map(appListEls, function(el){
                appList.push( $(el).next().text() );
            });
        params.push('app_list=' + appList.join(','));

        var gaiaRev = $(this.gaiaRevisionSel).text();
        params.push('gaia_rev=' + gaiaRev);

        var geckoRev = $(this.geckoRevisionSel).text();
        params.push('gecko_rev=' + geckoRev);

        var href = APPS_PAGE.urlBase + '?' + params.join('&');

        var inputEl = $(this.permalinkContainerSel).find("input");
        $(inputEl).val(href);

        $(this.permalinkContainerSel).css('display', 'block');

        $(inputEl).select();

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
        $(this.appTestName).text(name);
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

            $(idSel).text( datapointDatum[fieldName] );
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

    getAppData: function(context, fnSuccess, testIds, pageName, range, branch){

        var uri = '/' + APPS_PAGE.refData.project + '/testdata/test_values?' + 
            'branch=BRANCH&test_ids=TEST_IDS&page_name=PAGE_NAME&range=RANGE';

        uri = uri.replace('BRANCH', branch);
        uri = uri.replace('TEST_IDS', testIds);
        uri = uri.replace('PAGE_NAME', pageName);
        uri = uri.replace('RANGE', range);

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
