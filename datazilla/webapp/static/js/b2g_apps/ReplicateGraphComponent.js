/*******
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this file,
 * You can obtain one at http://mozilla.org/MPL/2.0/.
 * *****/
var ReplicateGraphComponent = new Class({

    Extends: Component,

    jQuery:'ReplicateGraphComponent',

    initialize: function(selector, options){

        this.setOptions(options);

        this.parent(options);

        this.view = new ReplicateGraphView();
        this.model = new ReplicateGraphModel();

        this.perfPlotClickEvent = 'PERF_PLOT_CLICK_EV';

        this.data = {};
        this.series = {};
        this.datapoint = {};
        this.chartData = {};
        this.hoverData = {};

        this.chartOptions = {
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

        $(this.view.appContainerSel).bind(
            this.perfPlotClickEvent, _.bind( this.getPlotData, this )
            );

        $(this.view.chartContainerSel).bind(
            'plothover', _.bind(this._hoverPlot, this)
            );
    },
    getPlotData: function(event, data){

        this.series = data.series;
        this.datapoint = data.datapoint;

        this.view.hideData();

        this.model.getReplicateData(
            this, this.renderPlot, this.datapoint.branch,
            this.datapoint.revision, this.datapoint.gecko_revision
            );

    },
    renderPlot: function(data){

        this.data = data;

        this.chartData = {
            'color':this.series['color'],
            'bars':{ 'show':true },
            'data':[]
            };

        var i=0;
        var j=0;
        var results = {};

        this.hoverData = {};

        var totalReplicates = 1;

        for(j=0; j<data.length; j++){

            results = data[j]['json_blob']['results'][this.datapoint.url];

            this.data[j]['replicate_range'] = { 'start':0, 'end':0 };
            this.data[j]['replicate_range']['start'] = totalReplicates;

            for(i=0; i<results.length; i++){

                this.chartData['data'].push( [ totalReplicates, results[i] ] );
                this.hoverData[ totalReplicates ] = j;

                totalReplicates++;
            }

            this.data[j]['replicate_range']['end'] = totalReplicates - 1;

            if( j === 0 ){
                this.view.setDetailContainer(
                    this.series, this.datapoint, this.data[j]);
            }

            this.view.showData();
        }

        this.plot = $.plot(
            $(this.view.chartContainerSel),
            [this.chartData],
            this.chartOptions
            );

        this.view.setHoverData(1, results[0]);

    },
    _hoverPlot: function(event, pos, item){

        if(!_.isEmpty(item)){
            var datum = this.chartData['data'][ item.dataIndex ];
            this.view.setHoverData(datum[0], datum[1]);
            var dataIndex = this.hoverData[ datum[0] ];

            if( this.data[dataIndex] ){
                this.view.setDetailContainer(this.series, this.datapoint, this.data[dataIndex]);
            }
        }
    }
});
var ReplicateGraphView = new Class({

    Extends:View,

    jQuery:'ReplicateGraphView',

    initialize: function(selector, options){

        this.setOptions(options);

        this.parent(options);

        this.appContainerSel = '#app_container';
        this.chartContainerSel = '#app_replicate_chart';
        this.buildDataContainerSel = '#app_replicate_build_data';
        this.replicateWaitSel = '#app_replicate_wait';
        this.replicateDataContainerSel = '#app_replicate_data_container';

        this.graphDetailClassSel = '.app-replicate-graph-detail';

        this.idPrefix = 'app_replicate_';
        this.idFields = [
            'application', 'replicate range', 'test', 'revision',
            'gecko_revision', 'avg', 'min', 'max', 'std'
            ];

    },
    showData: function(){
        $(this.replicateWaitSel).css('display', 'none');
        $(this.replicateDataContainerSel).css('display', 'block');
    },
    hideData: function(){
        $(this.replicateDataContainerSel).css('display', 'none');
        $(this.replicateWaitSel).css('display', 'block');
    },
    setHoverData: function(x, y){
        $('#' + this.idPrefix + 'x').text(x);
        $('#' + this.idPrefix + 'y').text(
            y.toString().slice(0, 10)
            );
        $('#' + this.idPrefix + 'y').attr('title', y);
    },
    setDetailContainer: function(seriesDatum, datapointDatum, jsonData){

       $(this.graphDetailClassSel).css(
            'background-color', seriesDatum.background_color
            );
         $(this.graphDetailClassSel).css(
            'border-color', seriesDatum.color
            );
        $(this.graphDetailCclassSel).css(
             'border-width', 1
             );

        var i = 0;
        var field = "";
        var idAttr = "";
        var value = "";

        for(i = 0; i<this.idFields.length; i++){
            field = this.idFields[i];
            idAttr = '#' + this.idPrefix + field;

            if(field === 'application'){
                value = seriesDatum.name;
            }else if(field === 'test'){
                value = datapointDatum.url;
            }else if(field === 'revision' || field === 'gecko_revision'){

                value = APPS_PAGE.getRevisionSlice(
                    jsonData['json_blob']['test_build'][field]
                    );

                $(idAttr).attr(
                    'title', jsonData['json_blob']['test_build'][field]
                    );

                if(field === 'revision'){
                    $(idAttr).attr(
                        'href',
                        APPS_PAGE.gaiaHrefBase + jsonData['json_blob']['test_build'][field]
                        );
                }else{
                    $(idAttr).attr(
                        'href',
                        APPS_PAGE.geckoHrefBase + jsonData['json_blob']['test_build'][field]
                        );
                }

            }else if(field === 'date'){

                value = this.convertTimestampToDate(
                    jsonData['json_blob']['testrun'][field], true
                    );

            }else{
                value = datapointDatum[field];
            }

            $(idAttr).text(value);
        }

        $(this.buildDataContainerSel).empty();

        var replicateRange = jsonData['replicate_range']['start'] + " - " +
            jsonData['replicate_range']['end'];

        this.loadField(
            'replicate range:',
            replicateRange,
            this.buildDataContainerSel
            );

        this.loadField(
            'date',
            this.convertTimestampToDate(
                jsonData['json_blob']['testrun']['date'], true
                ),
            this.buildDataContainerSel
            );

        this.loadField(
            'branch',
            jsonData['json_blob']['test_build']['branch'],
            this.buildDataContainerSel
            );

        this.loadField(
            'version',
            jsonData['json_blob']['test_build']['version'],
            this.buildDataContainerSel
            );

        this.loadField(
            'machine',
            jsonData['json_blob']['test_machine']['name'],
            this.buildDataContainerSel
            );

        this.loadField(
            'os',
            jsonData['json_blob']['test_machine']['os'],
            this.buildDataContainerSel
            );

        this.loadField(
            'os version',
            jsonData['json_blob']['test_machine']['osversion'],
            this.buildDataContainerSel
            );

        this.loadField(
            'platform',
            jsonData['json_blob']['test_machine']['platform'],
            this.buildDataContainerSel
            );

        if(jsonData['json_blob']['test_build']['build_revision']){

            var fullBuildRevision = jsonData['json_blob']['test_build']['build_revision'];
            var truncBuildRevision = APPS_PAGE.getRevisionSlice(fullBuildRevision);

            var divEl = $('<div></div>');
            $(divEl).addClass('app-control-element app-control-small-element app-build-data');
            $(divEl).append('Build Revision:');

            var aEl = $('<a></a>');
            $(aEl).attr('href', APPS_PAGE.buildHrefBase + fullBuildRevision);
            $(aEl).attr('target', '_blank');
            $(aEl).text(truncBuildRevision);

            $(divEl).append(aEl);

            $(this.buildDataContainerSel).append(divEl);
        }

    },
    loadField: function(fieldName, value, container){

        var divEl = $('<div></div>');
        $(divEl).addClass('app-control-element app-control-small-element app-build-data');
        $(divEl).append(fieldName + ':');

        var spanEl = $('<span></span>');
        $(spanEl).addClass('app-data');
        $(spanEl).text(value);

        $(divEl).append(spanEl);

        $(container).append(divEl);
    }
});
var ReplicateGraphModel = new Class({

    Extends:Model,

    jQuery:'ReplicateGraphModel',

    initialize: function(options){

        this.setOptions(options);

        this.parent(options);

    },

    getReplicateData: function(
        context, fnSuccess, branch, gaiaRevision, geckoRevision
        ){

        var uri = '/' + APPS_PAGE.refData.project +
            '/refdata/objectstore/json_blob/revisions?branch=' + branch +
            '&gaia_revision=' + gaiaRevision +
            '&gecko_revision=' + geckoRevision;

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
