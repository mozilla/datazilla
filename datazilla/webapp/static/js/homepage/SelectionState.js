/*******
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this file,
 * You can obtain one at http://mozilla.org/MPL/2.0/.
 * *****/
var SelectionState = new Class({

    jQuery:'SelectionState',

    initialize: function(selector, options){

        this.history = window.History;

        this.paramData = {};

        this.historyChange = false;

        this.stateChangeEvent = 'STATE_CHANGE_EV';

        this.hpContainerSel = '#hp_container';

        this.stateKeys = {
                'selected':false,
                'start':'',
                'stop':'',
                'product':'',
                'repository':'',
                'os':'',
                'os_version':'',
                'test':'',
                'page':'',
                'graph_search':'',
                'tr_id':'',
                'graph':'',
                'x86':'',
                'x86_64':'',
                'error_bars':'',
                'compare_product':'',
                'compare_repository':'',
                'compare_color':'',
            };

        this.defaultProject = 'talos';

        this.projectDefaults = {
            'b2g':{
                'product':'B2G',
                'repository':'master',
                'os':'',
                'os_version':'',
                'test':'phone',
                'page':'cold_load_time',
                'graph_search':''
                },
            'talos':{
                'product':'Firefox',
                'repository':'Mozilla-Inbound',
                'os':'mac',
                'os_version':'OS X 10.8',
                'test':'a11yr',
                'page':'',
                'graph_search':''
                },
            'webpagetest':{
                'product':'Firefox',
                'repository':'mozilla-central',
                'os':'WINNT',
                'os_version':'6.1',
                'test':'bc-win61i32-bldw:Firefox.Broadband',
                'page':'',
                'graph_search':''
                },
            'default':{
                'product':'',
                'repository':'',
                'os':'',
                'os_version':'',
                'test':'',
                'page':'',
                'graph_search':'',
                'tr_id':''
                }
            };

        this.selections = {};

        this.history.Adapter.bind(
            window, 'statechange', _.bind(this.stateChange, this)
            );
    },
    getSelectedProjectData: function(){

        var selectedProject = {};
        var project = "";
        for(project in this.selections){
            if(this.selections.hasOwnProperty(project)){
                if(this.selections[project]['selected'] === true){
                    selectedProject = this.selections[project];
                    selectedProject['project'] = project;
                }
            }
        }

        return selectedProject;
    },
    getProjectData: function(project){
        return this.selections[project];
    },
    setUrlObj: function(urlObj){

        var newState = {};
        newState.project = urlObj.param.query.project || this.defaultProject;

        this.setDefaults(newState.project);
        var selectedData = this.selections[newState.project];

        newState.start = parseInt(urlObj.param.query.start) || selectedData.start;
        newState.stop = parseInt(urlObj.param.query.stop) || selectedData.stop;
        newState.product = urlObj.param.query.product || selectedData.product;
        newState.repository = urlObj.param.query.repository || selectedData.repository;

        newState.test = urlObj.param.query.test || selectedData.test;
        newState.page = urlObj.param.query.page || selectedData.page;

        newState.os = urlObj.param.query.os || selectedData.os;
        newState.os_version = urlObj.param.query.os_version || selectedData.os_version;

        newState.arch = urlObj.param.query.arch || selectedData.arch;

        newState.graph_search = urlObj.param.query.graph_search || selectedData.graph_search;
        newState.tr_id = urlObj.param.query.tr_id || selectedData.tr_id;
        newState.graph = urlObj.param.query.graph || selectedData.graph;

        newState.x86 = urlObj.param.query.x86 || selectedData.x86;
        newState.x86_64 = urlObj.param.query.x86_64 || selectedData.x86_64;
        newState.error_bars = urlObj.param.query.error_bars || selectedData.error_bars;
        newState.compare_product = urlObj.param.query.compare_product || selectedData.compare_product;
        newState.compare_repository = urlObj.param.query.compare_repository || selectedData.compare_repository;
        newState.compare_color = urlObj.param.query.compare_color || selectedData.compare_color;

        this.resetState(newState);
    },
    setDefaults: function(project){

        if(this.selections[project] === undefined){

            this.selections[project] = jQuery.extend(true, {}, this.stateKeys);

            var defaults = {};
            if(this.projectDefaults[project] === undefined){
                defaults = this.projectDefaults['default'];
            }else{
                defaults = this.projectDefaults[project];
            }

            var projectKey = "";

            for(projectKey in defaults){
                this.selections[project][projectKey] = defaults[projectKey];
            }
        }
    },
    setProject: function(project){

        if(project === undefined){
            return;
        }

        this.setDefaults(project);
        this.selections[project]['selected'] = true;

        //Unselect any previously selected projects
        var p = "";
        for(p in this.selections){
            if(this.selections.hasOwnProperty(p)){
                if(p != project){
                    this.selections[p]['selected'] = false;
                }
            }
        }
    },
    setStart: function(project, start){

        this.setDefaults(project);

        var startInt = parseInt(start);

        if(!isNaN(startInt)){
            this.selections[project]['start'] = start;
        }
    },
    setStop: function(project, stop){

        this.setDefaults(project);

        var stopInt = parseInt(stop);

        if(!isNaN(stopInt)){
            this.selections[project]['stop'] = stopInt;
        }
    },
    setProduct: function(project, product){

        if(!_.isString(project)){
            return;
        }
        this.setDefaults(project);
        this.selections[project]['product'] = product;
    },
    setRepository: function(project, repository){

        if(!_.isString(repository)){
            return;
        }
        this.setDefaults(project);
        this.selections[project]['repository'] = repository;
    },
    setOs: function(project, os){

        if(!_.isString(os)){
            return;
        }
        this.setDefaults(project);
        this.selections[project]['os'] = os;
    },
    setOsVersion: function(project, osVersion){

        if(!_.isString(osVersion)){
            return;
        }
        this.setDefaults(project);
        this.selections[project]['os_version'] = osVersion;
    },
    setTest: function(project, test){
        if(!_.isString(test)){
            return;
        }
        this.setDefaults(project);
        this.selections[project]['test'] = test;
    },
    setPage: function(project, page){
        if(!_.isString(page)){
            return;
        }
        this.setDefaults(project);
        this.selections[project]['page'] = page;
    },
    setGraphSearch: function(project, terms){

        this.setDefaults(project);

        if(terms.length > 0){
            this.selections[project]['graph_search'] = terms.join(',');
        }else{
            this.selections[project]['graph_search'] = '';
        }
    },
    setTestRunId: function(project, testRunId, graphName){

        this.setDefaults(project);

        var trId = parseInt(testRunId);

        if(!isNaN( trId )){
            this.selections[project]['tr_id'] = trId;
        }

        this.selections[project]['graph'] = graphName;
    },
    setX86: function(project, boolStr){

        this.setDefaults(project);
        if(!_.isString(boolStr)){
            return;
        }
        this.selections[project]['x86'] = boolStr;

    },
    setX86_64: function(project, boolStr){

        this.setDefaults(project);
        if(!_.isString(boolStr)){
            return;
        }
        this.selections[project]['x86_64'] = boolStr;

    },
    setErrorBars: function(project, boolStr){

        this.setDefaults(project);
        if(!_.isString(boolStr)){
            return;
        }
        this.selections[project]['error_bars'] = boolStr;

    },
    setCompareProduct: function(project, product){

        if(!_.isString(project)){
            return;
        }
        this.setDefaults(project);
        this.selections[project]['compare_product'] = product;
    },
    setCompareRepository: function(project, repository){

        if(!_.isString(repository)){
            return;
        }
        this.setDefaults(project);
        this.selections[project]['compare_repository'] = repository;
    },
    setCompareColor: function(project, color){

        if(!_.isString(color)){
            return;
        }
        this.setDefaults(project);
        this.selections[project]['compare_color'] = color;
    },
    saveState: function(){

        //Don't save state for a history change
        if(this.historyChange === true){
            this.historyChange = false;
            return;
        }

        var params = this.getParams();

        this.history.pushState(
            {state:params},
            "Perf-o-Matic",
            '?' + params['params']
            );
    },
    resetState: function(newState){

        this.setProject(newState.project);
        this.setStart(newState.project, newState.start);
        this.setStop(newState.project, newState.stop);
        this.setProduct(newState.project, newState.product);
        this.setRepository(newState.project, newState.repository);
        this.setOs(newState.project, newState.os);
        this.setOsVersion(newState.project, newState.os_version);
        this.setTest(newState.project, newState.test);
        this.setPage(newState.project, newState.page);

        if( (newState.graph_search === undefined) || (newState.graph_search === '')){
            this.setGraphSearch(newState.project, []);
        }else{
            this.setGraphSearch(newState.project, newState.graph_search.split(','));
        }

        this.setTestRunId(newState.project, newState.tr_id, newState.graph);
        this.setX86(newState.project, newState.x86);
        this.setX86_64(newState.project, newState.x86_64);
        this.setErrorBars(newState.project, newState.error_bars);
        this.setCompareProduct(newState.project, newState.compare_product);
        this.setCompareRepository(newState.project, newState.compare_repository);
        this.setCompareColor(newState.project, newState.compare_color);
    },
    stateChange: function(){

        var historyState = this.history.getState();

        var params = this.getParams();

        if(this.isHistoryStateChange(historyState, params)){

            this.historyChange = true;

            this.setState(
                historyState.data.state.selected_data, params['selected_data']
                );

        }else {
            this.historyChange = false;
        }
    },
    setState: function(targetState, params){

        var stateKeys = _.keys(this.stateKeys);
        stateKeys.push('project');

        var state = '';

        for(var i=0; i < stateKeys.length; i++){

            state = stateKeys[i];

            if(targetState[state] != params[state]){

                //Any state in this conditional is different than the
                //current displayed state. Reset the selection state
                //to the one recovered from history
                this.resetState(targetState);

                //Execute parameter specific state recovery
                if (state === 'project') {

                    HOME_PAGE.SliderComponent.changeProject(
                        targetState.project
                        );

                    break;

                } else if ( (state === 'product') ||
                            (state === 'repository') ){

                    HOME_PAGE.SliderComponent.changeProductRepository(
                        targetState.product,
                        targetState.repository
                        );

                    break;

                } else if ( (state === 'start') ||
                            (state === 'stop') ){

                    HOME_PAGE.SliderComponent.changeSlider(
                        targetState.project,
                        targetState.start,
                        targetState.stop
                        );

                    break;

                } else if ( (state === 'os') ||
                            (state === 'os_version') ||
                            (state === 'test') ||
                            (state === 'page') ){

                    HOME_PAGE.NavComponent.nodeClick(
                        this.getMilliseconds(
                            targetState.start,
                            targetState.stop)
                            );

                    break;

                } else if ( (state === 'compare_product') ||
                            (state === 'compare_repository') ){

                    HOME_PAGE.NavComponent.setCompareDataSeries();

                } else if(state === 'x86'){
                    HOME_PAGE.LineGraphComponent.view.toggleX86();

                } else if(state === 'x86_64'){

                    HOME_PAGE.LineGraphComponent.view.toggleX86_64();

                } else if(state === 'error_bars'){

                    HOME_PAGE.LineGraphComponent.view.toggleErrorBars();
                }
            }
        }

        //graph_search and tr_id state recovery needs to execute after all
        //graphs are rendered
        if(targetState['graph_search'] != params['graph_search']){

            HOME_PAGE.LineGraphComponent.view.setSearchTerms(
                targetState.graph_search
                );

            HOME_PAGE.LineGraphComponent.view.search(false);
        }

        if(targetState['tr_id'] != params['tr_id']){
            HOME_PAGE.LineGraphComponent.changeReplicateGraph(targetState);
        }
    },
    getParams: function(){

        var selectedData = this.getSelectedProjectData();
        var params = {
            'params':'', 'hash':'', 'selected_data':selectedData
            };

        var pairs = _.pairs(selectedData);
        var pair = {};
        var i = 0;
        for(; i<pairs.length; i++){

            pair = pairs[i];

            if(pair[0] == 'selected'){
                continue;
            }

            if(pair[1] != ''){
                if(i == (pairs.length - 1)){
                    params['params'] += pair[0] + '=' + pair[1];
                }else {
                    params['params'] += pair[0] + '=' + pair[1] + '&';
                }
            }
        }

        params['hash'] = params['params'].hashCode();

        return jQuery.extend(true, {}, params);

    },
    isHistoryStateChange: function(historyState, paramData){

        var historyStateChange = false;

        if( (historyState.data.state != undefined) &&
            (historyState.data.state.hash != paramData.hash) ){
            historyStateChange = true;
        }

        return historyStateChange;

    },
    getParamsStrAndHash: function(params){

        var paramsStr = params.join('&');

        return { 'params_str':paramsStr,
                 'params':params,
                 'hash':paramsStr.hashCode() };
    },
    getMilliseconds: function(min, max){
        return {'min':parseInt(min*1000), 'max':parseInt(max*1000)};
    }
});
