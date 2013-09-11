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

        this.listData = {};

        this.view = new NavView();
        this.model = new NavModel();

        this.sliderSliceEvent = 'SLIDER_SLICE_EV';
        this.navClickEvent = 'NAV_CLICK_EV';

        $(this.view.hpContainerSel).bind(
            this.sliderSliceEvent, _.bind(this.loadLists, this)
            );

        $(this.view.compareOptionsSel).bind(
            'change', _.bind(this.loadCompareRepository, this)
            );

    },
    setCompareDataSeries: function(){
        this.view.initializeCompareSeries();
        $(this.view.compareOptionsSel).trigger('change');
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

            if( (os === "" && osVersion === "") ||
                (page != "") ){

                this.platformData = false;
                this.testData = true;

                //If the page is defined insure that os and
                //osVersion are "". This is required to over ride
                //the default os and osVersion when a url first
                //loads.
                os = "";
                osVersion = "";

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

        //Determine if there's a compare data series selected
        var selectedOption = $(this.view.compareOptionsSel).find(":selected");
        var productRepository = $(selectedOption).attr('internal_data');

        if(productRepository != undefined){

            productRepository = jQuery.parseJSON( productRepository.replace(/'/g, '"') );

            options.product = productRepository.p;
            options.branch = productRepository.b;
            options.fnSuccess = this.processCompareDataSeriesAndProcessData;
        }

        this.model.getAllData(options);

    },
    processCompareDataSeriesAndRenderGraphs: function(data){

        var options = {};
        options.test_graph = {};
        options.machine_graph = {};
        options.machines = {};
        options.compare_series = true;

        options = this.aggregateData(data, options);

        //Delete any previously set compare series
        HOME_PAGE.LineGraphComponent.deleteCompareDataSeries();

        //Load the compare data
        HOME_PAGE.LineGraphComponent.setCompareDataSeries(
            options.test_graph);

        //Render the graphs, no need to load data
        HOME_PAGE.LineGraphComponent.loadPerformanceGraphs({}, {});

    },
    processCompareDataSeriesAndProcessData: function(data){

        var options = {};
        options.test_graph = {};
        options.machine_graph = {};
        options.machines = {};
        options.compare_series = true;

        options = this.aggregateData(data, options);

        //Delete any previously set compare series
        HOME_PAGE.LineGraphComponent.deleteCompareDataSeries();

        //Load the compare data
        HOME_PAGE.LineGraphComponent.setCompareDataSeries(
            options.test_graph);

        var prData = HOME_PAGE.selectionState.getSelectedProjectData();

        var processDataOptions = {
            'project':prData.project,
            'product':prData.product,
            'branch':prData.repository,
            'os':prData.os,
            'os_version':prData.os_version,
            'test':prData.test,
            'page':prData.page,
            'start':prData.start,
            'stop':prData.stop,
            'context':this,
            'fnSuccess':this.processData };

        this.model.getAllData(processDataOptions);

    },
    processData: function(data){

        if(_.isEmpty(data.data)){

            var prData = HOME_PAGE.selectionState.getSelectedProjectData();
            this.view.showNoDataMessage(prData.product, prData.repository);
            return;
        }

        var options = {};

        options.test_graph = {};
        options.machine_graph = {};
        options.machines = {};
        options.compare_series = false;

        options = this.aggregateData(data, options);

        $(this.view.hpContainerSel).trigger(
            this.navClickEvent,
            { 'data':options.test_graph, 'machine_graph':options.machine_graph,
              'machines':options.machines } );

    },
    aggregateData: function(data, options){

        var obj = {};
        var i = 0;
        for(; i<data.data.length; i++){

            obj = data.data[i];

            if(options.compare_series === true){
                obj.type = 'compare';
            }

            if(options.machines[obj.mn] === undefined){
                options.machines[obj.mn] = { 'mn':obj.mn };
            }

            var platform = obj.osn + ' ' + obj.osv;
            var keyOne = "";
            if(this.testData){
                keyOne = platform;
            }else if(this.platformData){
                keyOne = obj.pu;
            }
            if( options.test_graph[keyOne] === undefined ){
                options.test_graph[keyOne] = [];
            }

            options.test_graph[keyOne].push(obj);

            if( options.machine_graph[obj.mn] === undefined ){
                options.machine_graph[obj.mn] = {
                    'count':0, 'test_eval':0, 'data':[]
                    };
            }

            //Load machine data
            options.machine_graph[obj.mn]['count']++;
            options.machine_graph[obj.mn]['test_eval'] += obj.te;
            options.machine_graph[obj.mn]['data'].push(obj);
        }

        return options;
    },
    loadCompareRepository: function(ev){

        HOME_PAGE.LineGraphComponent.view.hideGraphs();

        var selectedOption = $(this.view.compareOptionsSel).find(":selected");

        var productRepository = $(selectedOption).attr('internal_data');

        var prData = HOME_PAGE.selectionState.getSelectedProjectData();

        if(productRepository === undefined){
            /**
             Edge cases:
                1.) Same repo selected
                2.) No Product/Repository selected, clear out compare series
                3.) Selected Product/Repository has no data associated with it, 
                    message user
            ***/

            HOME_PAGE.selectionState.setCompareProduct(prData.project, "");
            HOME_PAGE.selectionState.setCompareRepository(prData.project, "");

            HOME_PAGE.selectionState.saveState();

            HOME_PAGE.LineGraphComponent.deleteCompareDataSeries();
            HOME_PAGE.LineGraphComponent.loadPerformanceGraphs({}, {});

        } else {

            productRepository = jQuery.parseJSON( productRepository.replace(/'/g, '"') );

            var options = {
                'project':prData.project,
                'product':productRepository.p,
                'branch':productRepository.b,
                'os':prData.os,
                'os_version':prData.os_version,
                'test':prData.test,
                'page':prData.page,
                'start':prData.start,
                'stop':prData.stop,
                'context':this,
                'fnSuccess':this.processCompareDataSeriesAndRenderGraphs
                };

            HOME_PAGE.selectionState.setCompareProduct(
                prData.project, productRepository.p);
            HOME_PAGE.selectionState.setCompareRepository(
                prData.project, productRepository.b);

            this.model.getAllData(options);

        }
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
        this.compareOptionsSel = '#hp_compare_options';

        this.menuTextLimit = 18;

    },
    initializeCompareSeries: function(){

        var prData = HOME_PAGE.selectionState.getSelectedProjectData();
        var optionValue = "";

        if( (prData.compare_product != "") &&
            (prData.compare_repository != "") ){

            optionValue = prData.compare_product + ' ' + prData.compare_repository;
            $(this.compareOptionsSel).val(optionValue);

        }else {
            optionValue = HOME_PAGE.SliderComponent.view.noProductRepositoryOptionValue;
        }

        $(this.compareOptionsSel).val(optionValue);

        if(prData.compare_color != ""){
            HOME_PAGE.LineGraphComponent.view.setCompareSeriesColor(
                prData.compare_color
                );
        }
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
