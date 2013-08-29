/*******
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this file,
 * *****/
var NavComponent = new Class({

    Extends: Component,

    jQuery:'NavComponent',

    initialize: function(selector, options){

        this.setOptions(options);

        this.parent(options);

        this.testData = false;
        this.platformData = false;

        //Used to indicate incoming data is from
        //a "Compare To" data series request
        this.compareSeries = false;

        this.listData = {};

        this.testGraph = {};
        this.machineGraph = {};
        this.machines = {};

        this.view = new NavView();
        this.model = new NavModel();

        this.sliderSliceEvent = 'SLIDER_SLICE_EV';
        this.navClickEvent = 'NAV_CLICK_EV';
        this.compareDataEvent = 'COMPARE_DATA_EV';

        $(this.view.hpContainerSel).bind(
            this.sliderSliceEvent, _.bind(this.loadLists, this)
            );

    },
    loadLists: function(ev, data){

        this.listData = data;

        this.view.setList(
            this.view.testMenuSel, this.nodeClick, this, data.data.tests,
            data.slider_min, data.slider_max);

        this.view.setList(
            this.view.platformMenuSel, this.nodeClick, this, data.data.platforms,
            data.slider_min, data.slider_max);

        //Simulate node click so we load a graph
        this.nodeClick({'min':data.slider_min, 'max':data.slider_max});

    },
    nodeClick: function(data){

        HOME_PAGE.LineGraphComponent.view.hideGraphs();

        var prData = HOME_PAGE.selectionState.getSelectedProjectData();

        var os = "";
        var osVersion = "";
        var test = "";
        var page = "";
        var noData = false;

        if(data.parent_sel === undefined){

            os = prData.os;
            osVersion = prData.os_version;
            test = prData.test;
            page = prData.page;

            if( _.isEmpty(this.listData.data.tests) &&
                _.isEmpty(this.listData.data.platforms) ){
                //There's no test data for this test datum
                noData = true;
            }

            if(os === "" && osVersion === ""){

                this.platformData = false;
                this.testData = true;

                if( test === "" && page === ""){
                    var keys = _.keys(this.listData.data.tests);
                    test = keys[0];

                    if(this.listData.data.tests[test] === undefined){
                        noData = true;
                    }else{
                        var values = _.keys(this.listData.data.tests[test]);
                        page = values[0];
                    }
                }

                data.nav = test + '->' + page;

            }else{

                this.platformData = true;
                this.testData = false;

                data.nav = os + ' ' + osVersion + '->' + test;
            }

        }else{

            if(this.view.platformMenuSel === data.parent_sel){

                this.platformData = true;
                this.testData = false;

                os = data.data.os;
                osVersion = data.data.version;
                test = data.key_two;

            }else if(this.view.testMenuSel === data.parent_sel){

                this.testData = true;
                this.platformData = false;

                test = data.key_one;
                page = data.key_two;
            }
        }
        if(noData === true){

            this.view.showNoDataMessage(
                this.listData.product, this.listData.repository
                );
            return;
        }

        if( (prData.product === "") || (prData.repository === "")){
            //No product/repository was specified in the url and the project
            //has no defaults set. In this case product/repository will not
            //be in the selection state. Save it now.
            HOME_PAGE.selectionState.setProduct(
                prData.project, this.listData.product
                );
            HOME_PAGE.selectionState.setRepository(
                prData.project, this.listData.repository
                );
        }

        HOME_PAGE.selectionState.setOs(prData.project, os);
        HOME_PAGE.selectionState.setOsVersion(prData.project, osVersion);
        HOME_PAGE.selectionState.setPage(prData.project, page);
        HOME_PAGE.selectionState.setTest(prData.project, test);

        this.view.setNav(data.nav);

        options = {
            'project':prData.project,
            'product':prData.product,
            'branch':prData.repository,
            'os':os,
            'os_version':osVersion,
            'test':test,
            'page':page,
            'start':parseInt(data.min/1000),
            'stop':parseInt(data.max/1000),
            'context':this,
            'fnSuccess':this.processData };

        this.model.getAllData(options);

    },
    getCompareSeriesData: function(product, repository){

        var prData = HOME_PAGE.selectionState.getSelectedProjectData();

        var options = {
            'project':prData.project,
            'product':product,
            'branch':repository,
            'os':prData.os,
            'os_version':prData.os_version,
            'test':prData.test,
            'page':prData.page,
            'start':prData.start,
            'stop':prData.stop,
            'context':this,
            'fnSuccess':this.processCompareSeriesData };

        this.model.getAllData(options);

    },
    processCompareSeriesData: function(data){

        this.testGraph = {};
        this.machineGraph = {};
        this.machines = {};

        this.compareSeries = true;

        _.map(data.data, _.bind(this.aggregateData, this));

        this.compareSeries = false;

        $(this.view.hpContainerSel).trigger(
            this.compareDataEvent,
            { 'compare_data':this.testGraph, 'machine_graph':this.machineGraph,
              'machines':this.machines } );
    },
    processData: function(data){

        if(_.isEmpty(data.data)){

            var prData = HOME_PAGE.selectionState.getSelectedProjectData();
            this.view.showNoDataMessage(prData.product, prData.repository);
            return;
        }

        this.testGraph = {};
        this.machineGraph = {};
        this.machines = {};

        _.map(data.data, _.bind(this.aggregateData, this));

        $(this.view.hpContainerSel).trigger(
            this.navClickEvent,
            { 'data':this.testGraph, 'machine_graph':this.machineGraph,
              'machines':this.machines } );

    },
    aggregateData: function(obj){

        if(this.compareSeries === true){
            obj.type = 'compare';
        }

        if(this.machines[obj.mn] === undefined){
            this.machines[obj.mn] = { 'mn':obj.mn };
        }

        //Initialize graph level 1
        var platform = obj.osn + ' ' + obj.osv;
        var keyOne = "";
        if(this.testData){
            keyOne = platform;
        }else if(this.platformData){
            keyOne = obj.pu;
        }
        if( this.testGraph[keyOne] === undefined ){
            this.testGraph[keyOne] = [];
        }

        if( this.machineGraph[obj.mn] === undefined ){
            this.machineGraph[obj.mn] = {
                'count':0, 'test_eval':0, 'data':[]
                };
        }
        this.testGraph[keyOne].push(obj);

        //Load machine data
        this.machineGraph[obj.mn]['count']++;
        this.machineGraph[obj.mn]['test_eval'] += obj.te;
        this.machineGraph[obj.mn]['data'].push(obj);
    }
});
var NavView = new Class({

    Extends:View,

    jQuery:'NavView',

    initialize: function(selector, options){

        this.setOptions(options);

        this.parent(options);

        this.hpContainerSel = '#hp_container';
        this.mainSpinnerSel = '#hp_main_wait';
        this.lineGraphSpinnerSel = '#hp_linegraph_wait';
        this.noDataSel = '#hp_no_data';
        this.testMenuSel = '#hp_test_menu';
        this.platformMenuSel = '#hp_platform_menu';
        this.navSel = '#hp_nav';


        this.menuTextLimit = 18;
    },
    setList: function(selector, callback, context, data, min, max){

        $(selector).empty();
        var listOrder = this.getAlphabeticalSortKeys(data);
        var datasetOne = {};
        var datasetTwo = {};
        var ulRoot = $(document.createElement('ul'));

        for(var i=0; i<listOrder.length; i++){

            datasetOne = data[ listOrder[i] ];
            var li = $(document.createElement('li'));
            var a = $(document.createElement('a'));

            $(a).text(this._getDisplayText(listOrder[i]));
            $(a).attr('title', listOrder[i]);
            $(li).append(a);

            var datasetOneSortOrder = this.getAlphabeticalSortKeys(datasetOne);
            var ul = $(document.createElement('ul'));
            $(li).append(ul);

            for(var j=0; j<datasetOneSortOrder.length; j++){

                var nestedLi = $(document.createElement('li'));
                var nestedA = $(document.createElement('a'));

                $(nestedA).text(this._getDisplayText(datasetOneSortOrder[j]));

                $(nestedA).attr('title', datasetOneSortOrder[j]);

                $(nestedA).bind('click', _.bind(
                    callback,
                    context,
                    { 'nav':listOrder[i] + '->' + datasetOneSortOrder[j],
                      'parent_sel':selector,
                      'key_one':listOrder[i],
                      'key_two':datasetOneSortOrder[j],
                      'min':min,
                      'max':max,
                      'data':data[listOrder[i]][datasetOneSortOrder[j]] }));

                $(nestedLi).append(nestedA);
                $(ul).append(nestedLi);
            }

            $(ulRoot).append(li);
        }

        $(selector).append(ulRoot);

        $(ulRoot).menu();

        this.showDataContainer();
    },
    hideDataContainer: function(){
        $(this.hpContainerSel).css('display', 'none');
        $(this.mainSpinnerSel).fadeIn();
    },
    showDataContainer: function(){
        $(this.mainSpinnerSel).css('display', 'none');
        $(this.hpContainerSel).fadeIn();

        HOME_PAGE.SliderComponent.resizeSlider();
    },
    setNav: function(navText){

        var truncatedText = navText;

        if(navText.length > 65){
            truncatedText = navText.slice(0, 55) + '...';
        }
        $(this.navSel).text(truncatedText);
        $(this.navSel).attr('title', navText);
    },
    showNoDataMessage: function(product, repository){

        var message = 'No data was found for the product, ' + product + ', and repository, ' + repository +
                      ', for the time range specified.';

        $(this.lineGraphSpinnerSel).css('display', 'none');
        $(this.noDataSel).fadeIn();
        $(this.noDataSel).text(message);

        HOME_PAGE.selectionState.saveState();
    },
    _getDisplayText: function(text){
        var displayText = text;
        if(text.length > this.menuTextLimit){
            displayText = displayText.slice(0, this.menuTextLimit) + '...';
        }
        return displayText;
    }
});
var NavModel = new Class({

    Extends:Model,

    jQuery:'NavModel',

    initialize: function(options){

        this.setOptions(options);

        this.parent(options);

    },
    getAllData: function(options){

        var uri = HOME_PAGE.urlBase +  options.project + '/testdata/all_data?';

        var keys = _.keys(options);

        var i = 0;
        for(; i < keys.length; i++){

            if( (options[ keys[i] ] === "") ||
                (keys[i] === 'fnSuccess') ||
                (keys[i] === 'context') ||
                (keys[i] === 'project')){

                continue;
            }

            if(i === keys.length - 1){
                uri += keys[i] + '=' + encodeURIComponent( options[ keys[i] ] );
            }else{
                uri += keys[i] + '=' + encodeURIComponent( options[ keys[i] ] ) + '&';
            }
        }

        jQuery.ajax( uri, {
            accepts:'application/json',
            dataType:'json',
            cache:false,
            type:'GET',
            context:options.context,
            success:options.fnSuccess,
        });
    }

});
