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

        $(this.view.hpContainerSel).bind(
            this.view.navClickEvent, _.bind(this.view.loadGraphs, this.view)
            );
    }
});
var LineGraphView = new Class({

    Extends:View,

    jQuery:'LineGraphView',

    initialize: function(selector, options){

        this.setOptions(options);

        this.parent(options);

        this.xaxisLabels = {};

        this.hpContainerSel = '#hp_container';
        this.lineGraphsSel = '#hp_linegraphs';
        this.tabContainerSel = '#hp_tabs';

        this.verticalTextClsSel = '.su-vertical-text';
        this.graphNameCls = 'hp-graph-name';

        this.navClickEvent = 'NAV_CLICK_EV';

        this.failColor = '#FF7700';
        this.passColor = '#44AA00';
        this.trendColor = '#A9A9A9';

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

        $(this.hpContainerSel).bind(
            'plothover', _.bind(this._hoverPlot, this)
            );

        this.minContainerHeight = 1000;
    },
    loadGraphs: function(ev, data){

        var sortedKeys = this.getAlphabeticalSortKeys(data.data);

        $(this.lineGraphsSel).empty();
        this.plots = {};

        var id = "", graphDiv = "", graphSel = "", labelDiv = "";

        var containerHeight = 45;
        var graphBlockHeight = 220;

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

            var pass = [], fail = [], trend = [], datum = "";

            for(var j=0; j<data.data[ sortedKeys[i] ].length; j++){

                datum = data.data[ sortedKeys[i] ][j];

                if(datum.te === 1){
                    pass.push( [ j, datum.m, datum ]);
                }else if(datum.te === 0){
                    fail.push([ j, datum.m, datum ]);
                }else{
                    pass.push([ j, datum.m, datum ]);
                }
                if(datum.tm != null){
                    trend.push([ j, datum.tm, datum ]);
                }

                if(this.xaxisLabels[graphSel] === undefined){
                    this.xaxisLabels[graphSel] = [];
                }
                this.xaxisLabels[graphSel][j] = this.convertTimestampToDate(
                    datum.pd || datum.dr
                    );
            }

            this.drawGraph(
                sortedKeys[i], pass, fail, trend, graphSel
                );

            $(graphDiv).append(labelDiv);

            containerHeight += graphBlockHeight;

        }

console.log([$(this.tabContainerSel), containerHeight]);
        if(containerHeight < this.minContainerHeight){
            containerHeight = this.minContainerHeight;
        }
        $(this.tabContainerSel).height(containerHeight);

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

            { 'color':this.trendColor,
              'data':trend,
              'points': {'show':true} } ];

        var chartOptions = jQuery.extend(true, {}, this.chartOptions);
        chartOptions['xaxis']['tickFormatter'] = _.bind(
            this.formatLabel, this, graphDivSel );

        this.plots[graphDivSel] = $.plot(
            $(graphDivSel),
            chart,
            chartOptions
            );
    },
    formatLabel: function(sel, label, axis){
        return this.xaxisLabels[sel][label] || "";
    },
    _hoverPlot: function(event, pos, item){
    }
});
var LineGraphModel = new Class({

    Extends:Model,

    jQuery:'LineGraphModel',

    initialize: function(options){

        this.setOptions(options);

        this.parent(options);

    }
});
