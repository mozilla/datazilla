/*******
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this file,
 * You can obtain one at http://mozilla.org/MPL/2.0/.
 * *****/
var LineGraphComponent = new Class({

    Extends: Component,

    jQuery:'LineGraphComponent',

    initialize: function(selector, options){

        this.setOptions(options);

        this.parent(options);

        this.view = new LineGraphView();
        this.model = new LineGraphModel();

        this.testRunIdCache = {};
        //The json data obj that the user last hovered over
        this.hoveredDataObj = {};

        $(this.view.hpContainerSel).bind(
            this.view.navClickEvent, _.bind(this.view.loadPerformanceGraphs, this.view)
            );

        $(this.view.hpContainerSel).bind(
            'plothover', _.bind(this.hoverPlot, this)
            );

        $(this.view.hpContainerSel).bind(
            'plotclick', _.bind(this.clickPlot, this)
            );
    },
    hoverPlot: function(event, pos, item){

        //Display detail panel
        if(_.isEmpty(item)){
            return;
        }

        if(event.target.id === this.view.replicatePanelSel.replace('#', '')){
            //User is hovering over the replicate graph
            this.replicateGraphHover(event, pos, item);
        }else{
            //User is hovering over line graphs, if the replicate display
            //is not locked show the replicates
            if(this.view.getLock() != true){
                this.lineGraphHover(event, pos, item);
            }
        }

    },
    lineGraphHover: function(event, pos, item){

        $(this.view.detailPanelSel).slideDown();

        var datum = item.series.data[item.dataIndex];

        if(_.isEmpty(datum[3])){
            return;
        }

        var testRunId = datum[3].ti;
        var page = datum[3].pu;

        if(datum[3].te === 0){
            this.view.replicateGraphColor = this.view.failColor;
        }else{
            this.view.replicateGraphColor = this.view.passColor;
        }

        var projectData = HOME_PAGE.selectionState.getSelectedProjectData();

        if(this.testRunIdCache[projectData.project] === undefined){
            this.testRunIdCache[projectData.project] = {};
        }

        var uri = "";

        if(this.testRunIdCache[projectData.project][testRunId] === undefined){

            this.view.hideReplicateGraph();

            this.testRunIdCache[projectData.project][testRunId] = { 'uri':"", 'data':{} };

            uri = this.model.getJsonObj(
                projectData, datum[3], this,
                _.bind(this.loadReplicates, this, testRunId,
                projectData.project, page));

            this.testRunIdCache[projectData.project][testRunId]['uri'] = uri;

        }else{

            this.hoveredDataObj = this.testRunIdCache[projectData.project][testRunId]['data'];

            this.view.renderReplicates(
                 page, this.testRunIdCache[projectData.project][testRunId]['data']
                );
        }

        uri = this.testRunIdCache[projectData.project][testRunId]['uri'];

        this.view.setJsonObjUrl(uri);

        this.view.loadHoverData(
            datum[3], this.view.toolDetailOne,
            this.view.hoverToolbarDetailsSel, this.view.datumInlineCls);

        this.view.loadHoverData(
            datum[3], this.view.hoverDetailOne,
            this.view.hoverDetailOneSel, this.view.datumCls);

        $(this.view.searchByMachineSel).text(datum[3].mn);
    },
    replicateGraphHover: function(event, pos, item){

        if( _.isEmpty(item) ){
            return;
        }

        this.view.setReplicateDetails(item.datapoint);

    },
    clickPlot: function(event, pos, item){

        //Display detail panel
        if(_.isEmpty(item)){
            return;
        }

        var datum = item.series.data[item.dataIndex];


        if(event.target.id === this.view.replicatePanelSel.replace('#', '')){
            //User clicked replicate graph
        }else{

            var lock = this.view.getLock();

            if(lock == true){

                //Replicates are already cached, just display them
                this.lineGraphHover(event, pos, item);

            }else{

                $(this.view.replicateLockSel).click();

            }

            //User clicked line graphs
            var revision = datum[3].r;

            this.view.addSearchTerm(revision);

            this.view.search();

        }

    },
    loadReplicates: function(testRunId, project, page, data){

        this.testRunIdCache[project][testRunId]['data'] = data;

        this.hoveredDataObj = data;

        this.view.renderReplicates(page, data);
    }
});
var LineGraphView = new Class({

    Extends:View,

    jQuery:'LineGraphView',

    initialize: function(selector, options){

        this.setOptions(options);

        this.parent(options);

        this.plots = {};
        this.xaxisLabels = {};
        this.replicatePlot = {};

        this.hpContainerSel = '#hp_container';
        this.lineGraphsSel = '#hp_linegraphs';
        this.lineGraphWaitSel = '#hp_linegraph_wait';
        this.tabContainerSel = '#hp_tabs';
        this.hoverToolbarDetailsSel = '#hp_toolbar_details';
        this.hoverDetailOneSel = '#hp_hover_detail_one';
        this.hoverDetailTwoSel = '#hp_hover_detail_two';

        this.verticalTextClsSel = '.hp-vertical-text';
        this.graphNameCls = 'hp-graph-name';

        this.detailPanelSel = '#hp_detail_panel';
        this.closeDetailPanelSel = '#hp_close_detail_panel';
        this.replicatePanelSel = '#hp_replicates';
        this.replicatePanelWaitSel = '#hp_replicate_wait';

        this.lightTextCls = 'hp-light-text';
        this.datumCls = 'hp-hover-datum';
        this.datumInlineCls = 'hp-hover-inline-datum';

        this.replicateNumSel = '#hp_replicate_num';
        this.replicateNumTimeSel = '#hp_replicate_run_time';
        this.replicateMinSel = '#hp_replicate_min';
        this.replicateMaxSel = '#hp_replicate_max';
        this.replicateLockSel = '#hp_replicate_lock';

        this.searchByMachineSel = '#hp_search_machine';

        this.inputSel = '#hp_input';
        this.viewJsonObjSel = '#hp_view_json_objects';

        this.navClickEvent = 'NAV_CLICK_EV';

        this.minContainerHeight = 1000;

        this.failColor = '#FF7700';
        this.passColor = '#44AA00';
        this.trendColor = '#A9A9A9';

        this.replicateGraphColor = this.passColor;

        this.replicateChartOptions = {
            'grid': {
                'clickable': true,
                'hoverable': true,
                'autoHighlight': true,
                'color': '#B6B6B6',
                'borderWidth': 0.5
            },

            'xaxis': {
            },

            'yaxis': {
                'autoscaleMargin':0.3
            },

            'series': {

                'points': {
                    'radius': 2.5
                }
            }
        };

        this.performanceChartOptions = {
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
                'min':1,
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

        this.x86ProcStr = '32bit';

        this.toolDetailOne = [
           [ undefined, ['r'] ],
           [ undefined, ['dr'], _.bind(this.formatTimestamp, this) ],
           [ undefined, ['pr'] ],
           [ 'avg', ['m'], _.bind(this.formatNumber, this) ],
           [ 'std', ['s'], _.bind(this.formatNumber, this) ],
           [ 'min', ['min'] ],
           [ 'max', ['max'] ]
            ];

        this.toolDetailTwo = [
           [ 'min', ['min'] ],
           [ 'max', ['max'] ]
            ];

        this.hoverDetailOne = [
           [ undefined, ['p', 'b', 'bv', 'osn', 'osv' ] ],
           [ 'test/page', ['tn', 'pu'] ],
           [ 'push date', ['pd'], _.bind(this.formatTimestamp, this) ],
           [ 'replicates', ['nr'] ],
           [ 'trend mean/std', ['tm', 'ts'], _.bind(this.formatNumber, this) ],
           [ 'p value/h0', ['pv', 'hr'], _.bind(this.formatNumber, this) ],
           [ 'fdr', ['f'] ],
            ];

        $(this.closeDetailPanelSel).bind('click', _.bind(function(e){
            $(this.detailPanelSel).slideUp();
            e.stopPropagation();
            }, this));

        $(this.closeDetailPanelSel).mouseover(function(e){
            $(this).css('cursor', 'pointer');
            });

        $(this.inputSel).focus(function(){
            this.select();
            });

        $(this.inputSel).bind('keypress',
            _.bind(function(e){
                var keyCode = e.keyCode;
                if(keyCode === 13){
                    this.search();
                }
                }, this)
            );
        $(this.inputSel).bind('keyup',
            _.bind(function(e){
                var keyCode = e.keyCode;
                if(keyCode === 8 || keyCode === 46){
                    this.search();
                }
                }, this)
            );

        $(this.searchByMachineSel).bind('click', _.bind(function(e){

            e.stopPropagation();

            var term = $(this.searchByMachineSel).text();
            this.addSearchTerm(term);
            this.search();

            }, this));

        $(window).resize(_.bind(this.resizePlots, this));

    },
    resizePlots: function(){

        this.resizeReplicatePlot();

        var width = $(this.lineGraphsSel).width();
        var key = "";
        for(key in this.plots){

            //Set the width on the graph container div
            $(this.plots[key]['graph_sel']).width(width);

            this.plots[key]['plot'].resize();
            this.plots[key]['plot'].setupGrid();
            this.plots[key]['plot'].draw();

        }
    },
    resizeReplicatePlot: function(){

        if( !_.isEmpty(this.replicatePlot) ){
            this.replicatePlot.resize();
            this.replicatePlot.setupGrid();
            this.replicatePlot.draw();
        }
    },
    search: function(){
        var terms = this.getSearchTerms();
        if(terms.length === 0){

            var key = "";
            for(key in this.plots){
                this.plots[key]['plot'].unhighlight();
            }

        }else{
            this.highlightPlots(terms);
        }
    },
    getSearchTerms: function(){
        var currentValue = $(this.inputSel).val();

        if(currentValue === ""){
            return [];
        }else{
            return _.map(currentValue.split(','), _.bind(function(item){

                if(item === 'x86'){
                    return this.x86ProcStr;
                }else{
                    return item.replace(/\s+/g, '');
                }
                }, this));
        }
    },
    addSearchTerm: function(term){

        var newValue = "";
        var currentValue = $(this.inputSel).val();

        if(term != ""){
            if(currentValue != ""){
                newValue = currentValue + ", " + term;
            }else{
                newValue = term;
            }

            var terms = this.getSearchTerms();
            //Insure search terms are not duplicated
            if(_.indexOf(terms, term) === -1){
                $(this.inputSel).val(newValue);
            }
        }
    },
    formatTimestamp: function(t){
        return this.convertTimestampToDate(parseInt(t), true);
    },
    formatNumber: function(n){
        return parseFloat(n).toFixed(2);
    },
    loadPerformanceGraphs: function(ev, data){

        var sortedKeys = this.getAlphabeticalSortKeys(data.data);

        $(this.lineGraphsSel).empty();

        this.plots = {};

        var id = "", graphDiv = "", graphSel = "", labelDiv = "";

        var containerHeight = 45;
        var graphBlockHeight = 220;

        var passSeriesIndex = 0;
        var failSeriesIndex = 1;
        var trendSeriesIndex = 2;

        for(var i=0; i<sortedKeys.length; i++){

            graphDiv = $(document.createElement('div'));
            id = 'line_graph_' + (i + 1);
            graphSel = '#' + id;
            $(graphDiv).attr('id', id);
            $(graphDiv).addClass('hp-line-plot');
            $(this.lineGraphsSel).append(graphDiv);

            labelDiv = $(document.createElement('div'));
            $(labelDiv).addClass(this.graphNameCls);
            $(labelDiv).text(sortedKeys[i]);

            data.data[ sortedKeys[i] ].sort(this.sortData);

            var pass = [], fail = [], trend = [], datum = "", searchKey = "";

            var highlightMap = {};
            var proc;

            for(var j=0; j<data.data[ sortedKeys[i] ].length; j++){

                datum = data.data[ sortedKeys[i] ][j];

                //Make a unique string for x86 so it doesn't highligh x86_64
                //when a search is done
                if(datum.pr == 'x86'){
                    proc = this.x86ProcStr;
                }else{
                    proc = datum.pr;
                }

                searchKey = datum.r + datum.mn + proc;

                if(datum.te === 1){
                    highlightMap[searchKey] = [
                        passSeriesIndex, pass.push( [ j, datum.m, datum.s, datum ]) - 1
                        ];

                }else if(datum.te === 0){

                    highlightMap[searchKey] = [
                        failSeriesIndex, fail.push([ j, datum.m, datum.s, datum ]) - 1
                        ];

                }else{

                    highlightMap[searchKey] = [
                        passSeriesIndex, pass.push([ j, datum.m, datum.s, datum ]) - 1
                        ];
                }

                if(datum.tm != null){
                    trend.push([ j, datum.tm, datum.s, datum ]);
                }

                if(this.xaxisLabels[graphSel] === undefined){
                    this.xaxisLabels[graphSel] = [];
                }
                this.xaxisLabels[graphSel][j] = this.convertTimestampToDate(
                    datum.pd || datum.dr
                    );
            }

            this.plots[graphSel] = {

                'plot':this.drawGraph(
                    sortedKeys[i], pass, fail, trend, graphSel
                    ),
                'highlight_map':highlightMap,

                'graph_sel':graphSel

                };

            $(graphDiv).append(labelDiv);

            containerHeight += graphBlockHeight;

        }

        if(containerHeight < this.minContainerHeight){
            containerHeight = this.minContainerHeight;
        }

        $(this.tabContainerSel).height(containerHeight);

        this.search();

        this.showGraphs();

        HOME_PAGE.selectionState.saveState();
    },
    sortData: function(a, b){
        //pd = push date
        //dr = date received

        //If we have a push date use it to sort in descending
        //order, otherwise use the date received
        if((a.pd != null) && (b.pd != null)){
            return a.pd - b.pd;
        }
        return a.dr - b.dr;
    },
    drawGraph: function(label, pass, fail, trend, graphDivSel){

        var chart = [
            { 'color':this.passColor,
              'data':pass,
              'points': {'show':true} },

            { 'color':this.failColor,
              'data':fail,
              'points': {'show':true} },

            //{ 'color':this.trendColor,
            //  'data':trend,
            //  'points': {'show':true} }
            ];

        var chartOptions = jQuery.extend(true, {}, this.performanceChartOptions);
        chartOptions['xaxis']['tickFormatter'] = _.bind(
            this.formatLabel, this, graphDivSel );

        //Account for resize of browser
        var width = $(this.lineGraphsSel).width();
        $(graphDivSel).width(width);

        return $.plot(
            $(graphDivSel),
            chart,
            chartOptions
            );
    },
    formatLabel: function(sel, label, axis){
        return this.xaxisLabels[sel][label] || "";
    },
    loadHoverData: function(datum, dataStruct, sel, datumClass){

        $(sel).empty();

        if(_.isEmpty(dataStruct)){
            return;
        }

        for(var i=0; i<dataStruct.length; i++){

            var fieldName = dataStruct[i][0];
            var fieldKeys = dataStruct[i][1];
            var formatValue = dataStruct[i][2];

            var fieldValue = "";
            var fieldsLen = fieldKeys.length;
            for(var j=0; j<fieldsLen; j++){
                if(datum[ fieldKeys[j] ] != undefined){

                    var v = "";
                    if(formatValue){
                        v = formatValue( datum[ fieldKeys[j] ] );
                    }else{
                        v = datum[ fieldKeys[j] ];
                    }

                    if( (fieldsLen > 1) && (j != (fieldsLen - 1))){
                        fieldValue += v + ', ';
                    }else {
                        fieldValue += v;
                    }
                }
            }

            if(fieldValue != ""){
                var el = $(document.createElement('div'));

                $(el).addClass(datumClass);

                if(fieldName === undefined){
                    $(el).text(fieldValue);
                }else{
                    var fnSpanEl = $(document.createElement('span'));
                    $(fnSpanEl).addClass(this.lightTextCls);
                    $(fnSpanEl).text(fieldName + ': ');
                    $(el).append(fnSpanEl);

                    var fvSpanEl = $(document.createElement('span'));
                    $(fvSpanEl).text(fieldValue);
                    $(el).append(fvSpanEl);
                }
                $(sel).append(el);
            }
        }
    },
    renderReplicates: function(page, data){

        if(_.isEmpty(data)){
            return;
        }

        $(this.replicatePanelSel).empty();

        var chartData = {
            'color':this.replicateGraphColor,
            'bars':{ 'show':true },
            'data':[]
            };

        var testName = "";
        var i=0;
        var j=0;
        var results = [];

        var totalReplicates = 1;

        var chartIndex = 0;
        var detailStructId = 0;
        var datapoint = [];
        var min = 0;
        var max = 0;

        for(j=0; j<data.length; j++){

            if(data[j]['testrun']['suite'].search(/tp5/) != -1){
                //Exlude first replicate
                results = data[j]['results'][page].slice(
                    1, data[j]['results'][page].length);

                totalReplicates++;

            }else{
                results = data[j]['results'][page];
            }

            if(results === undefined){
                continue;
            }
            for(i=0; i<results.length; i++){
                chartIndex = chartData['data'].push( [ totalReplicates, results[i] ] );
                if(chartIndex === 1){
                    detailStructId = j;
                    datapoint.push(totalReplicates);
                    datapoint.push(results[i]);
                    min = results[i];
                }

                if(results[i] < min){
                    min = results[i];
                }
                if(results[i] > max){
                    max = results[i];
                }
                totalReplicates++;
            }

        }

        this.setReplicateDetails(datapoint, min, max);

        this.showReplicateGraph();

        var width = $(this.replicatePanelSel).width();

        this.replicatePlot = $.plot(
            $(this.replicatePanelSel),
            [chartData],
            this.replicateChartOptions
            );
    },
    setReplicateDetails: function(datapoint, min, max){

        $(this.replicateNumSel).text(datapoint[0]);
        $(this.replicateNumTimeSel).text(this.formatNumber(datapoint[1]));

        if((min != undefined) && (max != undefined)){
            $(this.replicateMinSel).text(this.formatNumber(min));
            $(this.replicateMaxSel).text(this.formatNumber(max));
        }
    },
    highlightPlots: function(matchTargets){

        if(matchTargets.length === 0){
            return;
        }

        var matchString = new RegExp(matchTargets.join('|'));
        for(var plotSel in this.plots){
            for(var searchKey in this.plots[plotSel]['highlight_map']){
                if(searchKey.search(matchString) > -1){

                    this.plots[plotSel]['plot'].highlight(
                        this.plots[plotSel]['highlight_map'][searchKey][0],
                        this.plots[plotSel]['highlight_map'][searchKey][1]);

                    this.plots[plotSel]['plot'].draw();
                }else{
                    this.plots[plotSel]['plot'].unhighlight(
                        this.plots[plotSel]['highlight_map'][searchKey][0],
                        this.plots[plotSel]['highlight_map'][searchKey][1]);

                }
            }
        }
    },
    setJsonObjUrl: function(uri){
        $(this.viewJsonObjSel).attr('href', uri);
    },
    showGraphs: function(){

        $(this.lineGraphWaitSel).css('display', 'none');
        $(this.lineGraphsSel).fadeIn();

        //Need to resize after making visible to set width correctly
        this.resizePlots();
    },
    hideGraphs: function(){
        $(this.lineGraphsSel).css('display', 'none');
        $(this.lineGraphWaitSel).fadeIn();
    },
    showReplicateGraph: function(){

        $(this.replicatePanelWaitSel).css('display', 'none');
        $(this.replicatePanelSel).fadeIn();

        //Need to resize after making visible to set width correctly
        this.resizeReplicatePlot();
    },
    hideReplicateGraph: function(){

        $(this.replicatePanelSel).css('display', 'none');

        var width = $(this.replicatePanelSel).width();
        $(this.replicatePanelWaitSel).width(width);

        $(this.replicatePanelWaitSel).css('display', 'block');

        this.resizeReplicatePlot();
    },
    getLock: function(){
        return $(this.replicateLockSel).is(':checked');
    }
});
var LineGraphModel = new Class({

    Extends:Model,

    jQuery:'LineGraphModel',

    initialize: function(options){

        this.setOptions(options);

        this.parent(options);

    },
    getJsonObj: function(projectData, datum, context, fnSuccess){

        var uri = HOME_PAGE.urlBase +  projectData.project +
                '/testdata/raw/' + projectData.repository +
                '/' + datum.r + '?';

        uri += 'product=' + datum.p + '&os_name=' + datum.osn +
               '&os_version=' + datum.osv + '&branch_version=' + datum.bv +
               '&processor=' + datum.pr + '&build_type=' + datum.bt +
               '&test_name=' + datum.tn;

        jQuery.ajax( uri, {
            accepts:'application/json',
            dataType:'json',
            cache:false,
            type:'GET',
            context:context,
            success:fnSuccess,
        });

        return uri;
    }
});
