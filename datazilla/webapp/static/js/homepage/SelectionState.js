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
                'arch':'',
                'test':'',
                'page':''
            };

        this.defaultProject = 'talos';

        this.projectDefaults = {
            'b2g':{
                'product':'B2G',
                'repository':'master',
                'arch':'Gonk',
                'os':'Firefox OS',
                'os_version':'1.2.0.0-prerelease',
                'test':'phone',
                'page':''
                },
            'talos':{
                'product':'Firefox',
                'repository':'Mozilla-Inbound',
                'arch':'x86_64',
                'os':'mac',
                'os_version':'OS X 10.8',
                'test':'a11yr',
                'page':'',
                },
            'default':{
                'product':'Firefox',
                'repository':'Mozilla-Inbound',
                'arch':'x86_64',
                'test':'tp5o',
                'page':''
                }
            };

        this.selections = {};

        this.historyEvent = false;

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

        var project = urlObj.param.query.project || this.defaultProject;

        this.setDefaults(project);

        this.setProject(project);
        this.setArchitecture(urlObj.param.query.arch);
        this.setProduct(urlObj.param.query.product);
        this.setRepository(urlObj.param.query.repository);
        this.setTest(urlObj.param.query.test_name);
        this.setPage(urlObj.param.query.page);

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

        if(!_.isNumber(start)){
            return;
        }
        this.setDefaults(project);
        this.selections[project]['start'] = start;
    },
    setStop: function(project, stop){

        if(!_.isNumber(stop)){
            return;
        }
        this.setDefaults(project);
        this.selections[project]['stop'] = stop;
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
    setArchitecture: function(project, architecture){
        if(!_.isString(architecture)){
            return;
        }
        this.setDefaults(project);
        this.selections[project]['arch'] = architecture;
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
    saveState: function(){

        if( this.historyEvent === true ){
            this.historyEvent = false;
            return;
        }

        var params = this.getParams();

        this.history.pushState(
            {state:params},
            "Perf-o-Matic",
            '?' + params['params']
            );
    },
    stateChange: function(){

        var historyState = this.history.getState();

console.log(['stateChange', historyState]);

        var params = this.getParams();

        if(this.isHistoryStateChange(historyState, params)){

            var modifiedParams = this.getModifiedParams(
                historyState.data.state.hash, params.hash
                );

            this.historyEvent = true;

            //$(this.appContainerSel).trigger(
            //    this.stateChangeEvent, modifiedParams
            //    )
        }
    },
    getParams: function(){

        var selectedData = this.getSelectedProjectData();
        var params = {
            'params':'', 'hash':'', 'selected_data':selectedData
            };

        var pairs = _.pairs(selectedData);;
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

        return params;

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
    }
});
