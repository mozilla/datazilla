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

        //The firstGraphLoada property is used to recover graph_search and
        //tr_id state the first time graphs are rendered. graph_search
        //refers to the search string in the "Search Graphs:" input box and
        //tr_id refers to the test_run_id associated with the json replicate
        //structure displayed in the replicate display graph panel in the
        //bottom of the browser.
        this.firstGraphLoad = true;

        this.testRunIdCache = {};

        //The json data obj that the user last hovered over
        this.hoveredDataObj = {};

        $(this.view.hpContainerSel).bind(
            this.view.navClickEvent, _.bind(this.loadPerformanceGraphs, this)
            );

        $(this.view.hpContainerSel).bind(
            'plothover', _.bind(this.hoverPlot, this)
            );

        $(this.view.hpContainerSel).bind(
            'plotclick', _.bind(this.clickPlot, this)
            );

    },
    setCompareDataSeries: function(data){
        this.view.compareDataSeries = data;
        this.view.compareDataLoaded = false;
    },
    deleteCompareDataSeries: function(){

        this.view.compareDataSeries = {};
        var key = "";

        for(key in this.view.data.data){

            var noCompareData = _.reject( this.view.data.data[key], function(obj){

                return obj.type === 'compare';

                });

            this.view.data.data[key] = noCompareData;
        }
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
    loadPerformanceGraphs: function(ev, data){

        var projectData = {};

        if(this.firstGraphLoad === true){
            //First time loading graphs, set the search terms before graphs load
            projectData = HOME_PAGE.selectionState.getSelectedProjectData();
            this.view.setSearchTerms(projectData.graph_search);
        }

        //load the graphs
        this.view.loadPerformanceGraphs(ev, data);

        if(this.firstGraphLoad === true){
            //First time loading graphs, recover tr_id ( replicate graph
            //display state )
            this.changeReplicateGraph(projectData);

            this.firstGraphLoad = false;
        }
    },
    changeReplicateGraph: function(projectData){

        var key = projectData.graph;
        var datum = {};

        if(!_.isEmpty(this.view.data['data'][key])){
            var i = 0;
            for(; i < this.view.data['data'][key].length; i++){
                datum = this.view.data['data'][key][i];
                if(projectData.tr_id === datum.ti){
                   break;
                }
            }
        }

        if(!_.isEmpty(datum)){
            //Simulate plot click and supply datum
            this.clickPlot({ 'target':{ 'id':'' } }, {}, {}, datum);
        }
    },
    lineGraphHover: function(event, pos, item, datum){

        $(this.view.detailPanelSel).slideDown();

        if(_.isEmpty(datum)){

            if(item === null){
                return;
            }

            if(item.series.data[item.dataIndex]){
                datum = item.series.data[item.dataIndex][3];
            }

            //If datum is still empty here, user is hovering
            //over graph but not a data point
            if(_.isEmpty(datum)){
                return;
            }
        }

        var testRunId = datum.ti;
        var page = datum.pu;

        //Set the color for the replicate graph
        if(datum.type === 'compare'){
                this.view.replicateGraphColor = this.view.getCompareSeriesColor();
        }else{
            if(datum.te === 0){
                this.view.replicateGraphColor = this.view.failColor;
            }else{
                this.view.replicateGraphColor = this.view.passColor;
            }
        }

        var projectData = HOME_PAGE.selectionState.getSelectedProjectData();

        //Initialize the project
        if(this.testRunIdCache[projectData.project] === undefined){
            this.testRunIdCache[projectData.project] = {};
        }

        var uri = "";

        //First time we're seeing this testRunId, retrieve the data from the
        //database.
        if(this.testRunIdCache[projectData.project][testRunId] === undefined){

            this.view.hideReplicateGraph();

            this.testRunIdCache[projectData.project][testRunId] = { 'uri':"", 'data':{} };

            uri = this.model.getJsonObj(
                projectData.project, datum, this,
                _.bind(this.loadReplicates, this, testRunId,
                projectData.project, page));

            this.testRunIdCache[projectData.project][testRunId]['uri'] = uri;

        }else{
            //We have data for this testRunId retrieve it from the cache
            //structure
            this.hoveredDataObj = this.testRunIdCache[projectData.project][testRunId]['data'];

            this.view.renderReplicates(
                 page, this.testRunIdCache[projectData.project][testRunId]['data']
                );
        }

        //Retrieve th url
        uri = this.testRunIdCache[projectData.project][testRunId]['uri'];

        //Set the JSON object retrieval link
        this.view.setJsonObjUrl(uri);

        //Display reference data associated with the datum that doesn't
        //require database data retireval
        this.view.loadHoverData(
            datum, this.view.toolDetailOne,
            this.view.hoverToolbarDetailsSel, this.view.datumInlineCls);

        this.view.loadHoverData(
            datum, this.view.hoverDetailOne,
            this.view.hoverDetailOneSel, this.view.datumCls);

        //Set the machine display name
        $(this.view.searchByMachineSel).text(datum.mn);
    },
    replicateGraphHover: function(event, pos, item){

        if( _.isEmpty(item) ){
            return;
        }

        this.view.setReplicateDetails(item.datapoint);

    },
    clickPlot: function(event, pos, item, datum){

        if(_.isEmpty(datum)){

            if(item === null){
                return;
            }

            if(item.series.data[item.dataIndex]){
                datum = item.series.data[item.dataIndex][3];
            }

            //If datum is still empty here user is hovering
            //over graph but not a data point
            if(_.isEmpty(datum)){
                return;
            }
        }

        //Make sure we're not the replicate graph
        if(event.target.id != this.view.replicatePanelSel.replace('#', '')){

            var lock = this.view.getLock();

            if(lock == false){
                $(this.view.replicateLockSel).click();
            }

            this.lineGraphHover(event, pos, item, datum);

            //User clicked line graphs
            var revision = datum.r;

            this.view.addSearchTerm(revision);

            //Save the test_run_id and the selected graph in the selection state
            var projectData = HOME_PAGE.selectionState.getSelectedProjectData();
            HOME_PAGE.selectionState.setTestRunId(
                projectData.project, datum.ti, datum.graph);

            //Save the search terms including previous terms
            var terms = this.view.getSearchTerms();
            HOME_PAGE.selectionState.setGraphSearch(projectData.project, terms);

            //Save the state to add to history
            HOME_PAGE.selectionState.saveState();

            //Perform search without saving state since it's already saved
            this.view.search(false);
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

        this.data = {};
        this.plots = {};
        this.xaxisLabels = {};
        this.replicatePlot = {};
        this.compareDataSeries = {};

        this.hpContainerSel = '#hp_container';
        this.lineGraphsSel = '#hp_linegraphs';
        this.lineGraphWaitSel = '#hp_linegraph_wait';
        this.noDataSel = '#hp_no_data';
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

        //Graph container controls
        this.x86Sel = '#hp_x86';
        this.x8664Sel = '#hp_x86_64';
        this.errorBarsSel = '#hp_error_bars';
        this.compareSeriesColorSel = '#hp_compare_series_color';
        this.compareDataLoaded = false;

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
                'min':0,
                'autoscaleMargin':0.3
            },

            'zoom': {
                'interactive': true,
            },
            'pan': {
                'interactive': true,
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

        //This string is used as a replacement string for x86 so a search
        //for x86 won't highlight x86_64
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


        //This needs to be called before events are bound
        this.initializeToggles();

        this.initializeGraphControls();

        this.initializeGraphSearch();

        this.initializeDetailPanel();

        //Reset the plots to the browser size
        $(window).resize(_.bind(this.resizePlots, this));

        //Make sure the replicate lock is not selected
        $(this.replicateLockSel).attr('checked', false);

    },
    initializeToggles: function(){

        //Set the state of the toggle checkboxes according
        //to the selection state
        var prData = HOME_PAGE.selectionState.getSelectedProjectData();

        if(prData.x86 === 'false'){
            $(this.x86Sel).prop('checked', false);
            $(this.x86Sel).click();
        }

        if(prData.x86_64 === 'false'){
            $(this.x8664Sel).prop('checked', false);
            $(this.x8664Sel).click();
        }

        if(prData.error_bars === 'false'){
            $(this.errorBarsSel).prop('checked', false);
            $(this.errorBarsSel).click();
        }
    },
    initializeGraphControls: function(){

        $(this.x86Sel).bind('change', _.bind(function(ev){

            var checked = $(this.x86Sel).find('input').is(':checked');

            var boolStr = 'true';
            if(checked === false){
                boolStr = 'false';
            }

            var projectData = HOME_PAGE.selectionState.getSelectedProjectData();
            HOME_PAGE.selectionState.setX86(projectData.project, boolStr);

            this.hideGraphs();
            this.loadPerformanceGraphs(ev, {});

            }, this)
            );

        $(this.x8664Sel).bind('change', _.bind(function(ev){

            var checked = $(this.x8664Sel).find('input').is(':checked');
            var boolStr = 'true';
            if(checked === false){
                boolStr = 'false';
            }

            var projectData = HOME_PAGE.selectionState.getSelectedProjectData();

            HOME_PAGE.selectionState.setX86_64(projectData.project, boolStr);

            this.hideGraphs();
            this.loadPerformanceGraphs(ev, {});

            }, this)
            );

        $(this.errorBarsSel).bind('change', _.bind(function(ev){

            var checked = $(this.errorBarsSel).find('input').is(':checked');
            var boolStr = 'true';
            if(checked === false){
                boolStr = 'false';
            }

            var projectData = HOME_PAGE.selectionState.getSelectedProjectData();

            HOME_PAGE.selectionState.setErrorBars(projectData.project, boolStr);

            this.hideGraphs();
            this.loadPerformanceGraphs(ev, {});

            }, this)
            );

    },
    initializeGraphSearch: function(){

        $(this.inputSel).focus(function(){
            this.select();
            });

        $(this.inputSel).bind('keypress',
            _.bind(function(e){
                var keyCode = e.keyCode;
                if(keyCode === 13){
                    this.search(true);
                }
                }, this)
            );
        $(this.inputSel).bind('keyup',
            _.bind(function(e){
                var keyCode = e.keyCode;
                if(keyCode === 8 || keyCode === 46){
                    this.search(true);
                }
                }, this)
            );

    },
    initializeDetailPanel: function(){

        $(this.closeDetailPanelSel).bind('click', _.bind(function(ev){
            $(this.detailPanelSel).slideUp();
            ev.stopPropagation();
            }, this));

        $(this.closeDetailPanelSel).mouseover(function(ev){
            $(this).css('cursor', 'pointer');
            });

        $(this.searchByMachineSel).bind('click', _.bind(function(e){

            e.stopPropagation();

            var term = $(this.searchByMachineSel).text();
            this.addSearchTerm(term);
            this.search(true);

            }, this));

    },
    toggleX86: function(){

        var prData = HOME_PAGE.selectionState.getSelectedProjectData();

        if(prData.x86 === 'true'){
            $(this.x86Sel).prop('checked', true);
        }else {
            $(this.x86Sel).prop('checked', false);
        }

        $(this.x86Sel).click();
    },
    toggleX86_64: function(){

        var prData = HOME_PAGE.selectionState.getSelectedProjectData();

        if(prData.x86_64 === 'true'){
            $(this.x8664Sel).prop('checked', true);
        }else {
            $(this.x8664Sel).prop('checked', false);
        }

        $(this.x8664Sel).click();
    },
    toggleErrorBars: function(){

        var prData = HOME_PAGE.selectionState.getSelectedProjectData();

        if(prData.error_bars === 'true'){
            $(this.errorBarsSel).prop('checked', true);
        }else {
            $(this.errorBarsSel).prop('checked', false);
        }

        $(this.errorBarsSel).click();
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
    search: function(saveState){

        var terms = this.getSearchTerms();

        if(saveState === true){
            var projectData = HOME_PAGE.selectionState.getSelectedProjectData();
            HOME_PAGE.selectionState.setGraphSearch(projectData.project, terms);
            HOME_PAGE.selectionState.saveState();
        }

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
                        //Replace x86 string so we don't highlight x86_64
                        return this.x86ProcStr;
                    }else{
                        return item.replace(/\s+/g, '');
                    }

                }, this));
        }
    },
    setSearchTerms: function(terms){
        $(this.inputSel).val(terms);
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

        //Use class attribute data by default
        var targetData = {};
        if(!_.isEmpty(data.data)){
            //Set class attribute if data is not empty
            //this attribute is used for recovery of replicate
            //display state
            this.data = data;
            targetData = data;
        }else {
            targetData = this.data;
        }

        //Sort graphs to display alphabetically
        var sortedKeys = this.getAlphabeticalSortKeys(targetData.data);

        //Clean out the HTML container
        $(this.lineGraphsSel).empty();
        this.plots = {};


        var containerHeight = 45;
        var graphBlockHeight = 220;

        //These are the data indexes flot will use
        var passSeriesIndex = 0;
        var failSeriesIndex = 1;
        var compareSeriesIndex = 2;
        var trendSeriesIndex = 3;

        var filters = this.getFilters();

        if(filters['error_bars'] === true){
            this.performanceChartOptions.series.points.errorbars = 'y';
        }else{
            this.performanceChartOptions.series.points.errorbars = 'n';
        }

        var compareDataDefined = false;
        if(!_.isEmpty(this.compareDataSeries)){
            compareDataDefined = true;
        }

        var id = "", graphDiv = "", graphSel = "", labelDiv = "";

        for(var i=0; i<sortedKeys.length; i++){

            graphDiv = $(document.createElement('div'));
            id = 'line_graph_' + (i + 1);
            graphSel = '#' + id;

            $(graphDiv).attr('id', id);
            $(graphDiv).addClass('hp-line-plot');
            $(this.lineGraphsSel).append(graphDiv);

            labelDiv = this.setGraphLabelAndControls(
                graphDiv, sortedKeys[i], graphSel);

            //Add the compare data to the primary data structure before
            //implementing the sort. This will insure the ordering is
            //correct and prevent points from overlaying on top of one
            //another
            if( (compareDataDefined === true) &&
                (!_.isEmpty(this.compareDataSeries[ sortedKeys[i] ])) &&
                (this.compareDataLoaded === false) ){

                    targetData.data[ sortedKeys[i] ] = targetData.data[ sortedKeys[i] ].concat(
                        this.compareDataSeries[ sortedKeys[i] ]
                        );

            }

            targetData.data[ sortedKeys[i] ].sort(_.bind(this.sortData, this));

            var pass = [], fail = [], trend = [], compare = [],
                datum = "", compareDatum = "", searchKey = "";

            var highlightMap = {};
            var proc;
            for(var j=0; j<targetData.data[ sortedKeys[i] ].length; j++){

                datum = targetData.data[ sortedKeys[i] ][j];

                //Storing the graph name in sortedKeys
                //gives us a way to identify the graph associated with the
                //tr_id in the state management.
                datum['graph'] = sortedKeys[i];

                //Make a unique string for x86 so it doesn't highligh x86_64
                //when a search is done
                if(datum.pr == 'x86'){
                    proc = this.x86ProcStr;
                }else{
                    proc = datum.pr;
                }

                //Implement filter
                if(filters[datum.pr] === false){
                    continue;
                }

                searchKey = datum.r + datum.mn + proc;

                if(datum.type === 'compare'){

                    highlightMap[searchKey] = [
                        compareSeriesIndex, compare.push( [ j, datum.m, datum.s, datum ] ) - 1
                        ];

                }else {
                    //The datum.te attribute stands for test_evaluation, if it's
                    //1 the test passed and we display it as green, if it's 0
                    //it failed and it's displayed as orange to provide visual
                    //parity with other mozilla build/test data applications.
                    if(datum.te === 1){
                        highlightMap[searchKey] = [
                            passSeriesIndex, pass.push( [ j, datum.m, datum.s, datum ]) - 1
                            ];

                    }else if(datum.te === 0){

                        highlightMap[searchKey] = [
                            failSeriesIndex, fail.push([ j, datum.m, datum.s, datum ]) - 1
                            ];

                    }else{
                        //If datum.te is not set, default to pass and display as
                        //green
                        highlightMap[searchKey] = [
                            passSeriesIndex, pass.push([ j, datum.m, datum.s, datum ]) - 1
                            ];
                    }

                    if(datum.tm != null){
                        trend.push([ j, datum.tm, datum.s, datum ]);
                    }
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
                    sortedKeys[i], pass, fail, trend, compare, graphSel
                    ),
                'highlight_map':highlightMap,

                'graph_sel':graphSel

                };

            $(graphSel).bind('plotzoom plotpan', _.bind(function(graphSel){
                this.redrawOverlay(graphSel);
                }, this, graphSel));

            $(graphDiv).append(labelDiv);

            //Expand the size of the container to match the number of
            //graphs included in it.
            containerHeight += graphBlockHeight;

        }

        this.compareDataLoaded = true;

        //Set the container height according to total graphs displayed
        //but don't go below a minimum height requirement to give the
        //visual display some consistancy.
        if(containerHeight < this.minContainerHeight){
            containerHeight = this.minContainerHeight;
        }

        $(this.tabContainerSel).height(containerHeight);

        this.search(false);

        //Need to add the hover event listener to the zoom icons
        //after they're created
        $('.ui-icon').hover(
            function(ev){
                $(ev.currentTarget).css('cursor', 'pointer');
                },
            function(ev){
                $(ev.currentTarget).css('cursor', 'default');
                }
            );

        this.showGraphs();

        //All state relevant parameters are set at theis point, save
        //the overall state to the browser history.
        HOME_PAGE.selectionState.saveState();
    },
    setGraphLabelAndControls: function(graphDiv, label, graphSel){

        var labelDiv = $(document.createElement('div'));
        $(labelDiv).css('width', '100%');

        $(labelDiv).addClass(this.graphNameCls);
        $(labelDiv).text(label);

        var plusDiv = $(document.createElement('div'));
        $(plusDiv).addClass('ui-icon ui-icon-plus');
        $(plusDiv).attr('title', 'Click to zoom in');
        $(plusDiv).css('float', 'right');

        var minusDiv = $(document.createElement('div'));
        $(minusDiv).attr('title', 'Click to zoom out');
        $(minusDiv).addClass('ui-icon ui-icon-minus');
        $(minusDiv).css('float', 'right');

        $(plusDiv).bind('click', _.bind(this.zoomIn, this, graphSel));
        $(minusDiv).bind('click', _.bind(this.zoomOut, this, graphSel));

        $(labelDiv).append(plusDiv);
        $(labelDiv).append(minusDiv);

        return labelDiv;
    },
    zoomIn: function(graphSel){

        this.plots[graphSel].plot.zoom();
        this.redrawOverlay(graphSel);

    },
    zoomOut: function(graphSel){

        this.plots[graphSel].plot.zoomOut();
        this.redrawOverlay(graphSel);

    },
    redrawOverlay: function(graphSel){
        this.plots[graphSel].plot.triggerRedrawOverlay();
    },
    sortData: function(a, b){
        //pd = push date
        //dr = date received

        if((a.pd != null) && (b.pd != null)){
            //If the revision and the push date are the same between
            //a and b, it's a retrigger and we should order by the
            //date received instead of the push date.
            if( (a.r === b.r) && (a.pd === b.pd) ){
                return a.dr - b.dr;
            }else{
                //If we have a push date use it to sort in descending
                //order, otherwise use the date received
                return a.pd - b.pd;
            }
        }

        //sort by date received by default
        return a.dr - b.dr;
    },
    getFilters: function(){
        return {
            'x86':$(this.x86Sel).find('input').is(':checked'),
            'x86_64':$(this.x8664Sel).find('input').is(':checked'),
            'error_bars':$(this.errorBarsSel).find('input').is(':checked')
            };
    },
    getCompareSeriesColor: function(){
        //The input contains a hex value without the #
        return '#' + $(this.compareSeriesColorSel).val();
    },
    setCompareSeriesColor: function(color){
        $(this.compareSeriesColorSel).val(color);
    },
    drawGraph: function(label, pass, fail, trend, compare, graphDivSel){

        var chart = [
            { 'color':this.passColor,
              'data':pass,
              'points': {'show':true} },

            { 'color':this.failColor,
              'data':fail,
              'points': {'show':true} },

            { 'color':this.getCompareSeriesColor(),
              'data':compare,
              'points': {'show':true} },

            //Hiding the trend data to keep clutter out of the graph display
            //for now.

            //TODO: If we continue to calculate the trend values we could
            //conditionally display them based on a user selecting a
            //checkbox.

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
        var label = "";
        if(this.xaxisLabels[sel] != undefined){
            if(this.xaxisLabels[sel][label] != undefined){
                label = this.xaxisLabels[sel][label];
            }
        }
        return label;
    },
    loadHoverData: function(datum, dataStruct, sel, datumClass){
        //Display reference data associated with a datum. This
        //refernce data doesn't require additional database data
        //retrieval.

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

                    if(fieldKeys[0] === 'r'){

                        var truncatedField = fieldValue;
                        if(fieldValue.length > 12){
                            truncatedField = fieldValue.slice(0, 12) + '...';
                            $(el).text(truncatedField);
                        }else{
                            $(el).text(truncatedField);
                        }

                    }else{
                        $(el).text(fieldValue);
                    }

                    $(el).attr('title', fieldValue);

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

        //Display the replicate graph and associated reference data

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

        //Calulate the min and max dynamically
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

        $(this.noDataSel).css('display', 'none');
        $(this.lineGraphWaitSel).css('display', 'none');
        $(this.lineGraphsSel).fadeIn();

        //Need to resize after making visible to set width correctly
        this.resizePlots();
    },
    hideGraphs: function(){
        $(this.noDataSel).css('display', 'none');
        $(this.lineGraphsSel).css('display', 'none');
        $(this.lineGraphWaitSel).css('display', 'block');
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
    getJsonObj: function(project, datum, context, fnSuccess){

        var uri = HOME_PAGE.urlBase +  project +
                '/testdata/raw/' + datum.b + '/' + datum.r + '?';

        uri += 'product=' + encodeURIComponent(datum.p) + '&os_name=' + encodeURIComponent(datum.osn) +
               '&os_version=' + encodeURIComponent(datum.osv) + '&branch_version=' + encodeURIComponent(datum.bv) +
               '&processor=' + encodeURIComponent(datum.pr) + '&build_type=' + encodeURIComponent(datum.bt) +
               '&test_name=' + encodeURIComponent(datum.tn);

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
