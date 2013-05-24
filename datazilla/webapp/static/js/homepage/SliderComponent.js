/*******
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this file,
 * You can obtain one at http://mozilla.org/MPL/2.0/.
 * *****/
var SliderComponent = new Class({

    Extends: Component,

    jQuery:'SliderComponent',

    initialize: function(selector, options){

        this.setOptions(options);

        this.parent(options);

        this.view = new SliderView();
        this.model = new SliderModel();

        this.sliderSliceEvent = 'SLIDER_SLICE_EV';

        this.data = {};
        this.productRepositories = {};
        this.arch = {};
        this.machines = {};

        this.machinesGraph = {};

        this.sliderMin = 0;
        this.sliderMax = 0;

        $(this.view.sliderSel).bind(
            "valuesChanged", _.bind(this.getRange, this)
            );

        this.view.selectDefaultProject();

        this.getRange();

    },
    getRange: function(ev, data){

        //First data load
        if(!this.data[ HOME_PAGE.refData.project ]){

            this.model.getDataAllDimensions(
                HOME_PAGE.refData.project, this, this.loadData
                );

        }else{

            this.sliderMin = parseInt(data.values.min.getTime()/1000);
            this.sliderMax = parseInt(data.values.max.getTime()/1000);

            var dl = this.data[ HOME_PAGE.refData.project ].length - 1;

            //Get the last data point
            var lastDate = parseInt(
                this.data[HOME_PAGE.refData.project][dl].dr - 1
                );
            if(this.sliderMin < lastDate){

                this.model.getDataAllDimensions(
                    HOME_PAGE.refData.project, this, this.loadData,
                    this.sliderMin, lastDate
                    );
            }else{

                this.getTimeSlice();

                $(this.view.hpContainerSel).trigger(
                    this.sliderSliceEvent,
                    { 'machine_graph':this.machineGraph,
                      'test_graph':this.testGraph,
                      'platform_graph':this.platformGraph,
                      'graph_size':this.graphSize,
                      'slider_min':this.sliderMin,
                      'slider_max':this.sliderMax }
                    );

            }
        }
    },
    getTimeSlice: function(){

        this.productRepositories = {};
        this.arch = {};
        this.machines = {};

        this.testGraph = {};
        this.platformGraph = {};
        this.machineGraph = {};

        this.graphSize = 0;

        var productRepositoryData = $(this.view.productRepositorySel).attr(
            'internal_data');

        var archData = $(this.view.archSel).attr('internal_data');

        var productFilter = "", repositoryFilter = "", archFilter = "";

        if(productRepositoryData){
            var pr = jQuery.parseJSON(productRepositoryData);
            productFilter = pr.p;
            repositoryFilter = pr.b;
        }else{
            productFilter = HOME_PAGE.refData.product;
            repositoryFilter = HOME_PAGE.refData.repository;
        }

        if(archData){
            var ar = jQuery.parseJSON(ar);
            archFilter = ar.pr;
        }else{
            archFilter = HOME_PAGE.refData.arch;
        }

        var platform = "";

        _.map(
            this.data[HOME_PAGE.refData.project],
            function(obj){
                if( (obj.dr >= this.sliderMin) &&
                    (obj.dr <= this.sliderMax) ){

                    productRepository = [obj.p, obj.b].join(' ');

                    if(this.productRepositories[productRepository] === undefined){
                        this.productRepositories[productRepository] = {
                            'b':obj.b, 'p':obj.p
                            };
                    }

                    if(this.arch[obj.pr] === undefined){
                        this.arch[obj.pr] = { 'pr':obj.pr };
                    }

                    if(this.machines[obj.mn] === undefined){
                        this.machines[obj.mn] = { 'mn':obj.mn };
                    }

                    //Filter conditions
                    if( ( obj.p === productFilter ) &&
                        ( obj.b === repositoryFilter ) &&
                        ( obj.pr === archFilter ) ){

                        platform = obj.osn + ' ' + obj.osv;

                        //Initialize graph level 1
                        if( this.testGraph[ obj.tn] === undefined ){
                            this.testGraph[obj.tn] = {};
                        }
                        if( this.platformGraph[platform] === undefined ){
                            this.platformGraph[platform] = {};
                        }
                        if( this.machineGraph[obj.mn] === undefined ){
                            this.machineGraph[obj.mn] = {
                                'count':0, 'test_eval':0, 'data':[]
                                };
                        }

                        //Initialize graph level 2
                        if( this.testGraph[obj.tn][obj.pu] === undefined ){
                            this.testGraph[obj.tn][obj.pu] = {};
                        }
                        if( this.platformGraph[platform][obj.tn] === undefined ){
                            this.platformGraph[platform][obj.tn] = {};
                        }

                        //Initialize graph level 3
                        if( this.testGraph[obj.tn][obj.pu][platform] === undefined ){
                            this.testGraph[obj.tn][obj.pu][platform] = [];
                        }
                        if( this.platformGraph[platform][obj.tn][obj.pu] === undefined ){
                            this.platformGraph[platform][obj.tn][obj.pu] = [];
                        }

                        this.testGraph[obj.tn][obj.pu][platform].push(obj);
                        this.platformGraph[platform][obj.tn][obj.pu].push(obj);

                        //Load machine data
                        this.machineGraph[obj.mn]['count']++;
                        this.machineGraph[obj.mn]['test_eval'] += obj.te;
                        this.machineGraph[obj.mn]['data'].push(obj);

                        this.graphSize++;
                    }
                }
                }, this );

        this.view.setSelectMenu(
            this.view.productRepositorySel, this.productRepositories,
            HOME_PAGE.refData.product
            );
        this.view.setSelectMenu(
            this.view.archSel, this.arch,
            HOME_PAGE.refData.arch
            );
        this.view.setSelectMenu(
            this.view.machinesSel, this.machines,
            HOME_PAGE.refData.machine
            );
    },
    loadData: function(data){

        if( this.data[HOME_PAGE.refData.project] === undefined){
            this.data[HOME_PAGE.refData.project] = [];
        }

        this.data[HOME_PAGE.refData.project] = this.data[HOME_PAGE.refData.project].concat(data['data']);


        if(!this.slider){

            //Initialize slider
            var maxDate = 0;
            var minDate = 0;

            var dates = this.getMinMaxDate(data);

            this.sliderMin = dates.min;
            this.sliderMax = dates.max;

            this.slider = $(this.view.sliderSel).dateRangeSlider({
                'arrows':true,
                'bounds': {
                    min: new Date(parseInt(data['min_date_data_received']*1000)),
                    max: new Date(parseInt(dates.max)),
                    },
                'defaultValues': {
                    min: new Date(parseInt(dates.min)),
                    max: new Date(parseInt(dates.max)),
                    }
                });
        }

        this.getTimeSlice();

        $(this.view.hpContainerSel).trigger(
            this.sliderSliceEvent,
            { 'machine_graph':this.machineGraph,
              'test_graph':this.testGraph,
              'platform_graph':this.platformGraph,
              'graph_size':this.graphSize,
              'slider_min':this.sliderMin,
              'slider_max':this.sliderMax }
            );
    },
    getMinMaxDate: function(data){

        var dates = { 'min':0, 'max':0 };

        if(this.data[HOME_PAGE.refData.project].length > 0){

            dates['max'] = this.data[HOME_PAGE.refData.project][0].dr*1000;
            minIndex = this.data[ HOME_PAGE.refData.project ].length - 1;
            dates['min'] = this.data[HOME_PAGE.refData.project][minIndex].dr*1000;

        }else{

            dates['max'] = data['min_date_data_received']*1000;
            dates['min'] = data['start']*1000;
        }

        return dates;
    }
});
var SliderView = new Class({

    Extends:View,

    jQuery:'SliderView',

    initialize: function(selector, options){

        this.setOptions(options);

        this.parent(options);

        this.hpContainerSel = '#hp_container';
        this.sliderSel = '#slider';
        this.tabSel = '#hp_tabs';

        this.projectSel = '#hp_project';
        this.productRepositorySel = '#hp_repository';
        this.archSel = '#hp_arch';
        this.machinesSel = '#hp_machines';

        $(this.tabSel).tabs();

    },
    setSelectMenu: function(selector, selectOptions, optionDefault){

        var keys = this.getAlphabeticalSortKeys(selectOptions);
        var i = 0;
        var data = "";
        var option = "";

        var value = $(selector).prop('value');

        $(selector).empty();

        for(; i<=keys.length; i++){
            if(keys[i] != undefined){

                data = JSON.stringify(selectOptions[keys[i]]).replace(/"/g, "'"); 
                option = $('<option></option>');
                $(option).text(keys[i]);
                $(option).prop('value', keys[i]);
                $(option).attr('internal_data', data);

                $(selector).append(option);
            }
        }

        var defaultSelection = value;
        if(!defaultSelection){
            defaultSelection = optionDefault;
        }

        $(selector).val(defaultSelection);
    },
    selectDefaultProject: function(){
        $(this.projectSel).val(HOME_PAGE.refData.project);
    }
});
var SliderModel = new Class({

    Extends:Model,

    jQuery:'SliderModel',

    initialize: function(options){

        this.setOptions(options);

        this.parent(options);

    },
    getDataAllDimensions: function(project, context, fnSuccess, start, stop){

        var uri = HOME_PAGE.urlBase +  project + '/testdata/all_data';

        if(start && stop){
            uri += '?start=' + start + '&stop=' + stop;
        }

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
