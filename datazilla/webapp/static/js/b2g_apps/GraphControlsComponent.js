/*******
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this file,
 * You can obtain one at http://mozilla.org/MPL/2.0/.
 * *****/
var GraphControlsComponent = new Class({

    Extends: Component,

    jQuery:'GraphControlsComponent',

    initialize: function(selector, options){

        this.setOptions(options);

        this.parent(options);

        this.view = new GraphControlsView();
        this.model = new GraphControlsModel();

        this.appLookup = {};
        this.testLookup = {};
        this.branchLookup = {};

        this.model.getApps(this, this.initializeAppList);

        this.appToggleEvent = 'APP_TOGGLE_EV';
        this.testToggleEvent = 'TEST_TOGGLE_EV';

        this.excludeList = {
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
    initializeAppList: function(data){

        var sortOrder = this.view.getAlphabeticalSortKeys(data);

        var colorIndex = 0;
        var colorCount = this.view.colors.length - 1;
        var hexColor = "";

        for(var i=0; i<sortOrder.length; i++){

            var seriesDatum = data[ sortOrder[i] ];

            if( this.excludeList[ seriesDatum.name ] ){
                continue;
            }

            if(colorIndex > colorCount){
                colorIndex = 0;
            }

            hexColor = this.view.colors[colorIndex];
            colorIndex++;

            this.view.getSeriesLabel(
                this.view.datasetLegendSel, hexColor, seriesDatum,
                this.toggleAppSeries, this, this.view.appSeriesContainerSel,
                this.view.appSeriesIdPrefix
                );

            seriesDatum['color'] = hexColor;
            this.appLookup[ seriesDatum.id ] = seriesDatum;
        }

        this.model.getBranches(this, this.initializeBranchList);

    },
    initializeBranchList: function(data){

        var keys = _.keys(data).sort();

        var branch = "";
        var i = 0;

        for(i = 0; i<keys.length; i++){

            branch = data[ keys[i] ].branch;
            if(!this.branchLookup[branch]){
                this.branchLookup[branch] = true;
                this.view.addBranch(branch);
            }
        }

        //Make sure apps and branches are loaded before tests are initialized
        this.model.getTests(this, this.initializeTestList);
    },
    initializeTestList: function(data){

        var sortOrder = this.view.getAlphabeticalSortKeys(data);

        for(var i=0; i<sortOrder.length; i++){

            var seriesDatum = data[ sortOrder[i] ];

            if( this.excludeList[ seriesDatum.url ] ){
                continue;
            }

            this.view.getSeriesLabel(
                this.view.datasetTestLegendSel, this.view.testColor,
                seriesDatum, this.toggleTestSeries, this,
                this.view.testSeriesContainerSel,
                this.view.testSeriesIdPrefix
                );

            this.testLookup[ seriesDatum.id ] = seriesDatum;
        }

        var inputEls = $(this.view.testSeriesContainerSel).find('input');
        $(inputEls[0]).click();
    },
    toggleAppSeries: function(event){

        var idAttr = $(event.currentTarget).parent().parent().attr('id');
        var id = this.view.getId(idAttr);

        $(this.view.appContainerSel).trigger(
            this.appToggleEvent,
            { 'test_id':id }
            );

    },
    toggleTestSeries: function(event){

        var idAttr = $(event.currentTarget).parent().parent().attr('id');
        var id = this.view.getId(idAttr);

        var eventData = this.testLookup[id];

        this.view.selectApplications(eventData.test_ids);

        for( var tId in eventData['test_ids'] ){

            eventData['test_ids'][ tId ] = {
                'name':this.appLookup[ tId ]['name'],
                'color':this.appLookup[ tId ]['color']
                };
        }

        $(this.view.appContainerSel).trigger(
            this.testToggleEvent, eventData
            );

    }
});
var GraphControlsView = new Class({

    Extends:View,

    jQuery:'GraphControlsView',

    initialize: function(selector, options){

        this.setOptions(options);

        this.parent(options);

        this.appSeriesContainerSel = '#app_series';
        this.testSeriesContainerSel = '#test_series';

        this.branchSelectMenuSel = '#app_branch';

        this.idRegex = /^.*_(\d+)$/;

        this.colors = [
            '#0b3b40', '#99911c', '#a66247', '#7989b3', '#8bccc4', '#a35dd9', '#ff622e', '#cc8bc7', '#2254bf', '#22bf90', '#666345', '#ffbead', '#481059', '#2c96f2', '#10593d', '#ffc42e', '#4c1a0e', '#add9ff', '#196612', '#332409', '#604e73', '#103859', '#3dbf22', '#7f5717', '#462eff', '#1e84a6', '#88b379', '#f2cea5', '#1e1ea6', '#2cdbf2', '#d4f22c', '#e58729', '#091233', '#a61e88', '#ff2ee3', '#f2eba5'
            ];

        this.testColor = '#5CB2CB';

        this.appContainerSel = '#app_container';

        this.defaultBranchOption = 'v1-train';

        //series label ids
        this.datasetLegendSel = '#su_legend';
        this.datasetTestLegendSel = '#su_test_legend';
        this.datasetTitleName = 'su_dataset_title';
        this.datasetCbContainerName = 'su_dataset_cb';
        this.datasetCloseName = 'su_dataset_close';
        this.appSeriesIdPrefix = 'app_series_';
        this.testSeriesIdPrefix = 'test_series_';
    },
    selectApplications: function(testIds){

        var inputEls = $(this.appSeriesContainerSel).find('input');
        var inputEl = "";
        var idAttr = "";
        var id = "";
        var checked = "";

        for(var i=0; i<inputEls.length; i++){

            inputEl = inputEls[i];
            idAttr = $(inputEl).parent().parent().attr('id');
            checked = $(inputEl).attr('checked');
            id = this.getId(idAttr);

            if(id in testIds){
                if(!checked){
                    $(inputEl).click();
                }
            }else{
                if(checked){
                    $(inputEl).click();
                }
            }
        }
    },
    getSeriesLabel: function(
        legendIdSel, hexColor, seriesDatum, fnCallback, context,
        containerSel, idPrefix
        ){

        var rgbAlpha = this.hexToRgb(hexColor);

        var label = "";
        if(seriesDatum['url']){
            label = seriesDatum.url;
        }else{
            label = seriesDatum.name;
        }

        var legendClone = $(legendIdSel).clone();
        $(legendClone).attr(
            'id', idPrefix + seriesDatum.id
            );

        var inputEl = $(legendClone).find('input');
        $(inputEl).bind('click', _.bind( fnCallback, context ) );

        var titleDiv = $(legendClone).find(
            '[name="' + this.datasetTitleName + '"]'
            );

        $(titleDiv).text( label );

        $(legendClone).css('background-color', rgbAlpha);
        $(legendClone).css('border-color', hexColor);
        $(legendClone).css('border-width', 1);
        $(legendClone).css('display', 'block');

        $(legendClone).hover(
            function(){
                //On mouseOver
                $(this).css('background-color', '#FFFFFF');
            },
            function(){
                //On mouseOut
                $(this).css('background-color', rgbAlpha);
            }
        );

        $(containerSel).append(legendClone);

    },
    getId: function(idAttr){
        var id = "";
        if(idAttr){
            var idMatch = this.idRegex.exec(idAttr);
            if(idMatch && idMatch.length === 2){
                id = idMatch[1];
            }
        }
        return id;
    },
    addBranch: function(branch){
        var optionEl = $('<option></option>');
        $(optionEl).attr('value', branch);

        if(branch === this.defaultBranchOption){
            $(optionEl).attr('selected', 'selected');
        }

        $(optionEl).text(branch);
        $(this.branchSelectMenuSel).append(optionEl);
    }
});
var GraphControlsModel = new Class({

    Extends:Model,

    jQuery:'GraphControlsModel',

    initialize: function(options){

        this.setOptions(options);

        this.parent(options);

    },

    getBranches: function(context, fnSuccess){

        var uri = '/' + APPS_PAGE.refData.project + '/refdata/perftest/ref_data/products';

        jQuery.ajax( uri, {
            accepts:'application/json',
            dataType:'json',
            cache:false,
            type:'GET',
            data:data,
            context:context,
            success:fnSuccess,
        });
    },
    getApps: function(context, fnSuccess){

        var uri = '/' + APPS_PAGE.refData.project + '/refdata/perftest/ref_data/tests';

        jQuery.ajax( uri, {
            accepts:'application/json',
            dataType:'json',
            cache:false,
            type:'GET',
            data:data,
            context:context,
            success:fnSuccess,
        });
    },

    getTests: function(context, fnSuccess){

        var uri = '/' + APPS_PAGE.refData.project + '/refdata/perftest/ref_data/pages';

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
