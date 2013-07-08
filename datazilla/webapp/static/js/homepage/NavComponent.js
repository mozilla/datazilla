/*******
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this file,
 * You can obtain one at http://mozilla.org/MPL/2.0/.
 * *****/
var NavComponent = new Class({

    Extends: Component,

    jQuery:'NavComponent',

    initialize: function(selector, options){

        this.setOptions(options);

        this.parent(options);

        this.testData = false;
        this.platformData = false;

        this.testGraph = {};
        this.machineGraph = {};
        this.machines = {};

        this.view = new NavView();
        this.model = new NavModel();

        this.sliderSliceEvent = 'SLIDER_SLICE_EV';
        this.navClickEvent = 'NAV_CLICK_EV';

        $(this.view.hpContainerSel).bind(
            this.sliderSliceEvent, _.bind(this.loadLists, this)
            );

    },
    loadLists: function(ev, data){

        this.view.setList(
            this.view.testMenuSel, this.nodeClick, this, data.data.tests,
            data.data.min, data.data.max);

        this.view.setList(
            this.view.platformMenuSel, this.nodeClick, this, data.data.platforms,
            data.data.min, data.data.max);
    },
    nodeClick: function(data){

        this.view.setNav(data.nav);

        var prData = HOME_PAGE.selectionState.getSelectedProjectData();

        var os = "";
        var osVersion = "";
        var test = "";
        var page = "";

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

        HOME_PAGE.selectionState.setOs(prData.project, os);
        HOME_PAGE.selectionState.setOsVersion(prData.project, osVersion);
        HOME_PAGE.selectionState.setPage(prData.project, page);
        HOME_PAGE.selectionState.setTest(prData.project, test);

        //HOME_PAGE.selectionState.setTest(project, prData.product);

        //$(this.hpContainerSel).trigger(this.navClickEvent, data);
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
    processData: function(data){

        this.testGraph = {};
        this.machineGraph = {};
        this.machines = {};

        _.map(data.data, _.bind(this.aggregateData, this));

console.log([this.navClickEvent, data]);
        $(this.view.hpContainerSel).trigger(
            this.navClickEvent,
            { 'data':this.testGraph, 'machine_graph':this.machineGraph,
              'machines':this.machines } );

    },
    aggregateData: function(obj){

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
    },
    setNav: function(navText){
        $(this.navSel).text(navText);
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
                uri += keys[i] + '=' + options[ keys[i] ];
            }else{
                uri += keys[i] + '=' + options[ keys[i] ] + '&';
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
