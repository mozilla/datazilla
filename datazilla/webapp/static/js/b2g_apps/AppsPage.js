/*******
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this file,
 * You can obtain one at http://mozilla.org/MPL/2.0/.
 * *****/

APPS_PAGE = {};

var AppsPage = new Class( {

    Extends: Page,

    jQuery:'AppsPage',

    initialize: function(selector, options){

        this.parent(options);
        this.revisionLength = 16;

        this.gaiaHrefBase = "https://github.com/mozilla-b2g/gaia/commit/";
        this.geckoHrefBase = "http://git.mozilla.org/?p=releases/gecko.git;a=commit;h=";
        this.buildHrefBase = "https://github.com/mozilla-b2g/platform_build/commit/";

        this.history = window.History;

        this.stateChangeEvent = 'STATE_CHANGE_EV';

        this.appContainerSel = '#app_container';

        //If it's set to true the STATE_CHANGE_EV is from a
        //change in history (back/forward button clicked)
        this.historyEvent = false;

        //If set to true, it disables the abbility to saveState
        //this allows component defined events to specify whether
        //they are added to the history
        this.disableSaveState = false;

        this.history.Adapter.bind(
            window, 'statechange', _.bind(this.stateChange, this)
            );

        this.paramKeys = [ 'branch', 'range', 'test', 'app', 'app_list',
                           'gaia_rev', 'gecko_rev' ];

        this.excludeList = {
            'ftu':true,
            'marketplace':true,
            'b2g_gaia_launch_perf': true,
            'gallery_load_end': true,
            'camera_load_end': true,
            'phone_time_to_paint': true,
            'music_time_to_paint': true,
            'music_load_end': true,
            'messages_load_end': true,
            'messages_time_to_paint': true,
            'phone_load_end': true,
            'camera_time_to_paint': true,
            'settings_load_end': true,
            'gallery_time_to_paint': true,
            'settings_time_to_paint': true,
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

        var view = this.performanceGraphComponent.view;

        var params = [];
        var lookup = {};

        var branch = $(view.branchSel).find(":selected").text();
        if(branch != ""){
            params.push('branch=' + branch);
            lookup['branch'] = branch;
        }

        var device = $(view.deviceSel).find(":selected").text();
        if(device != ""){
            params.push('device=' + device);
            lookup['device'] = device;
        }

        var range = $(view.timeRangeSel).find(":selected").val();
        if(range != ""){
            params.push('range=' + range);
            lookup['range'] = range;
        }

        var test = $(view.testSeriesSel).find('input:checked').next().text();
        if(test != ""){
            params.push('test=' + test);
            lookup['test'] = test;
        }

        var appListEls = $(view.appSeriesSel).find("input:checkbox:checked");
        var appList = [];
        _.map(appListEls, function(el){
                appList.push( $(el).next().text() );
            });
        if(appList.length > 0){
            params.push('app_list=' + appList.join(','));
        }
        //Always store the app_list lookup so we can represent
        //0 selected apps in the app_list
        lookup['app_list'] = appList;

        var app = $(view.appNameSpanSel).text();
        //If there's only one app in the applist or the app
        //is not in the app_list make sure the selected app
        //is set to the first app in app_list
        if((appList.length === 1) ||
           (_.lastIndexOf(appList, app) === -1) ){

            app = appList[0];
        }

        if( (app != "") && (appList.length > 0)){
            params.push('app=' + app);
            lookup['app'] = app;
        }


        var gaiaRev = $(view.gaiaRevisionSel).text();
        if(gaiaRev != ""){
            params.push('gaia_rev=' + gaiaRev);
            lookup['gaia_rev'] = gaiaRev;
        }

        var geckoRev = $(view.geckoRevisionSel).text();
        if(geckoRev != ""){
            params.push('gecko_rev=' + geckoRev);
            lookup['gecko_rev'] = geckoRev;
        }

        return { 'params':params , 'lookup':lookup };

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
        this.refData.project = urlObj.seg.path[0];

        if(urlObj.attr.directory.search(/\/$/) === -1){
            urlObj.attr.directory += '/';
        }

        this.urlBase = urlObj.attr.base + urlObj.attr.directory;

        this.defaults = {};
        this.defaults['branch'] = urlObj.param.query.branch;
        this.defaults['device'] = urlObj.param.query.device || 'inari';
        this.defaults['range'] = urlObj.param.query.range;
        this.defaults['test'] = urlObj.param.query.test || 'cold_load_time';
        this.defaults['app'] = urlObj.param.query.app;

        if( urlObj.param.query.app_list != undefined ){

            var appLookup = {};

            _.map(
                urlObj.param.query.app_list.split(','),
                function(app){
                    appLookup[app] = true;
                }
                );

            this.defaults['app_list'] = appLookup;
        }

        this.defaults['gaia_rev'] = urlObj.param.query.gaia_rev;
        this.defaults['gecko_rev'] = urlObj.param.query.gecko_rev;

    },
    getRevisionSlice: function(revision){
        return revision.slice(0, this.revisionLength);
    },
    stateChange: function(){

        this.setRefData();

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

        var key = "";
        var modifiedParams = {};
        var i  = 0;

        for(i=0; i < this.paramKeys.length; i++){

            key = this.paramKeys[i];

            if(oldParams[key] != newParams[key]){
                modifiedParams[key] = oldParams[key];
            }
        }

        var keyHash = this.getDatapointHashCode(
            oldParams['app'], oldParams['gaia_rev'],
            oldParams['gecko_rev']
            );

        modifiedParams['datapoint_hash'] = keyHash;

        return modifiedParams;
    },
    getDatapointHashCode: function(appName, gaiaRevision, geckoRevision){

        var key = appName +
                  this.getRevisionSlice(gaiaRevision) +
                  this.getRevisionSlice(geckoRevision);
        return key.hashCode();
    }

});

$(document).ready(function() {

    APPS_PAGE = new AppsPage();

    APPS_PAGE.setRefData();

    APPS_PAGE.graphControlsComponent = new GraphControlsComponent();
    APPS_PAGE.performanceGraphComponent = new PerformanceGraphComponent();
    APPS_PAGE.replicateGaphComponent = new ReplicateGraphComponent();


});
