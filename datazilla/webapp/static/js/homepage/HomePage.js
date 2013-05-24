/*******
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this file,
 * You can obtain one at http://mozilla.org/MPL/2.0/.
 * *****/

HOME_PAGE = {};

var HomePage = new Class( {

    Extends: Page,

    jQuery:'HomePage',

    initialize: function(selector, options){

        this.parent(options);

        this.projectDefaults = {
            'default':{
                'product':'Firefox',
                'repository':'Mozilla-Inbound',
                'arch':'x86_64',
                }
            };

    },
    saveState: function(){

        if( (this.historyEvent === true) || (this.disableSaveState === true) ){
            this.historyEvent = false;
            return;
        }

        var params = this.getParams();
        var paramData = this.getParamsStrAndHash(params.params);

        paramData['lookup'] = params['lookup'];

        this.history.pushState(
            {state:paramData},
            "Perf-o-Matic",
            //this.refData.project + '?' + paramData['params_str']
            '?' + paramData['params_str']
            );

    },
    getParams: function(){

    },
    getParamsStrAndHash: function(params){

        var paramsStr = params.join('&');

        return { 'params_str':paramsStr,
                 'params':params,
                 'hash':paramsStr.hashCode() };
    },
    setRefData: function(){

        this.refData = {};

        var urlObj = jQuery.url(window.location).data;

        this.refData.project = urlObj.param.query.project || 'jeads';

        var defaults = {};
        if(this.projectDefaults[this.refData.project] === undefined){
            defaults = this.projectDefaults['default'];
        }else{
            defaults = this.projectDefaults[this.refData.project];
        }

        this.refData.arch = urlObj.param.query.arch || defaults.arch;
        this.refData.product = urlObj.param.query.product || defaults.product;
        this.refData.repository = urlObj.param.query.repository || defaults.repository;

        if(urlObj.attr.directory.search(/\/$/) === -1){
            urlObj.attr.directory += '/';
        }

        this.urlBase = urlObj.attr.base + urlObj.attr.directory;

    },
    stateChange: function(){

        this.setRefData();
        /*

        var historyState = this.history.getState();
        var params = this.getParams();
        var paramData = this.getParamsStrAndHash(params.params);

        if(this.isHistoryStateChange(historyState, paramData)){

            var modifiedParams = this.getModifiedParams(
                historyState.data.state.lookup, params.lookup
                );

            this.historyEvent = true;

            $(this.appContainerSel).trigger(
                this.stateChangeEvent, modifiedParams
                )
        }
        */
    },
    isHistoryStateChange: function(historyState, paramData){

        var historyStateChange = false;

        if( (historyState.data.state != undefined) &&
            (historyState.data.state.hash != paramData.hash) ){
            historyStateChange = true;
        }

        return historyStateChange;
    },
    getModifiedParams: function(oldParams, newParams){

    }

});

$(document).ready(function() {

    HOME_PAGE = new HomePage();

    HOME_PAGE.setRefData();

    HOME_PAGE.SliderComponent = new SliderComponent();
    HOME_PAGE.NavComponent = new NavComponent();
    HOME_PAGE.LineGraphComponent = new LineGraphComponent();

});
