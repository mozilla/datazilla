/*******
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this file,
 * You can obtain one at http://mozilla.org/MPL/2.0/.
 * *****/
var SliderComponent = new Class({

    Extends: Component,

    jQuery:'SliderComponent',

    initialize: function(selector, options){

        /****************
         Object attributes coming back from all dimension
         web services

         ti:"test_run_id",
         dr:"date received",
         r:"revision",
         p:"product",
         b:"branch",
         bv:"branch version",
         osn:"operating system",
         osv:"operating system version",
         pr:"processor",
         bt:"build type",
         mn:"machine name",
         pi:"pushlog_id",
         pd:"push date",
         tn:"test name",
         pu:"page url",
         m:"mean",
         s:"std",
         hr:"h0 rejected",
         pv:"p value",
         nr:"replicates",
         f:"false discovery rate",
         tm:"trend mean",
         ts:"trend std",
         te:"test evaluation"


         this.data[project][product][branch][test] = [];

        *******************/

        this.setOptions(options);

        this.parent(options);

        this.view = new SliderView();
        this.model = new SliderModel();

        this.sliderSliceEvent = 'SLIDER_SLICE_EV';

        this.sliders = {};
        this.data = {};
        this.productRepositories = {};
        this.arch = {};
        this.machines = {};

        $(this.view.sliderSel).bind(
            "valuesChanged", _.bind(this.getRange, this)
            );

        $(this.view.projectSel).bind(
            "change", _.bind(this.setProjectOption, this)
            );

        $(this.view.productRepositorySel).bind(
            "change", _.bind(this.setProductRepositoryOption, this)
            );

        this.view.selectDefaultProject();

        this.model.getProductRepositories(
            this, _.bind(this.loadProductRepositories, this)
            );

    },
    setProjectOption: function(ev){

        var project = $(this.view.projectSel).find(":selected").val();

        //Set refData
        HOME_PAGE.refData.project = project;

        if(this.productRepositories[project] != undefined){
            this.loadProductRepositories(this.productRepositories);
        }else {
            this.model.getProductRepositories(
                this, _.bind(this.loadProductRepositories, this)
                );
        }

        this.view.setSelectMenu(
            this.view.productRepositorySel, this.productRepositories[project],
            this.getProductRepositoryString(
                HOME_PAGE.refData.product, HOME_PAGE.refData.repository
                )
            );
    },
    loadProductRepositories: function(data){

        var id = 0;
        var productRepository = "";
        var project = HOME_PAGE.refData.project;

        //First time loading data
        if(this.productRepositories[project] === undefined){

            this.productRepositories[project] = {};

            var product = "";
            var branch = "";

            for(id in data){

                if(data.hasOwnProperty(id)){
                    //Some data is corrupted in production with the
                    //string 'undefined'. Exclude this data.
                    if( (data[id]['product'] === 'undefined') ||
                        (data[id]['branch'] === 'undefined') ){

                        continue;
                    }

                    productRepository = data[id]['product'] + ' ' + data[id]['branch'];

                    branch = data[id]['branch'];
                    product = data[id]['product'];

                    if(this.productRepositories[project][productRepository] === undefined){
                        this.productRepositories[project][productRepository] = {
                            'b':branch, 'p':product
                            };
                    }

                    if(this.data[project] === undefined){
                        this.data[project] = {};
                    }

                    if(this.data[project][product] === undefined){
                        this.data[project][product] = {};
                    }

                    if(this.data[project][product][branch] === undefined){
                        this.data[project][product][branch] = [];
                    }

                    if(this.sliders[project] === undefined){

                        this.sliders[project] = {
                            'el':'', 'id':this.view.sliderIdBase + '_' + project,
                            'min':0, 'max':0
                            };
                    }
                }
            }
        }

        this.view.setSelectMenu(
            this.view.productRepositorySel, this.productRepositories[project],
            this.getProductRepositoryString(product, branch)
            );

        this.view.setSliderEl(project, this.sliders);
        this.getRange();
    },
    setProductRepositoryOption: function(ev){

        var selectedOption = $(this.view.productRepositorySel).find(":selected");
        var data = $(selectedOption).attr('internal_data');
        data = this.getInternalDataObject(data);

        HOME_PAGE.refData.product = data.p;
        HOME_PAGE.refData.repository = data.b;

    },
    getRange: function(ev, data){

        var project = HOME_PAGE.refData.project;
        var product = HOME_PAGE.refData.product;
        var repository = HOME_PAGE.refData.repository;

        if(this.data[project] === undefined){
            //First data load for the project
            this.model.getDataAllDimensions(
                project, product, repository, this, this.loadData
                );

        }else{

            this.sliders[project].min = parseInt(data.values.min.getTime()/1000);
            this.sliders[project].max = parseInt(data.values.max.getTime()/1000);

            var dl = this.data[project][product][repository].length - 1;

            //Get the last data point
            var lastDate = parseInt(
                this.data[project][product][repository][dl].dr - 1
                );

            if(this.sliders[project].min < lastDate){
                //Data out of range retrieve new data
                this.model.getDataAllDimensions(
                    project, product, repository, this, this.loadData,
                    this.sliders[project].min, lastDate
                    );
            }else{

                //Data already loaded retrieve slice
                this.getTimeSlice();

                $(this.view.hpContainerSel).trigger(
                    this.sliderSliceEvent,
                    { 'machine_graph':this.machineGraph,
                      'test_graph':this.testGraph,
                      'platform_graph':this.platformGraph,
                      'graph_size':this.graphSize,
                      'slider_min':this.sliders[project].min,
                      'slider_max':this.sliders[project].min }
                    );

            }
        }
    },
    getTimeSlice: function(){

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

        var project = HOME_PAGE.refData.project;
        var product = HOME_PAGE.refData.product;
        var repository = HOME_PAGE.refData.repository;

        if(productRepositoryData){
            var pr = jQuery.parseJSON(
                this.getInternalDataObject(productRepositoryData)
                );
            productFilter = pr.p;
            repositoryFilter = pr.b;
        }else{
            productFilter = product;
            repositoryFilter = repository;
        }

        if(archData){
            archFilter = jQuery.parseJSON(ar).pr;
        }else{
            archFilter = HOME_PAGE.refData.arch;
        }

        _.map(
            this.data[project][product][repository],
            _.bind(
                this.aggregateData, this, productFilter,
                repositoryFilter, archFilter, project )
            );

        this.view.setSelectMenu(
            this.view.archSel, this.arch,
            HOME_PAGE.refData.arch
            );
    },
    aggregateData: function(productFilter, repositoryFilter, archFilter, project, obj){

        if( (obj.dr >= this.sliders[project].min) &&
            (obj.dr <= this.sliders[project].max) ){

            productRepository = this.getProductRepositoryString(obj.p, obj.b);

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
    },
    getProductRepositoryString: function(product, repository){
        return product + ' ' + repository;
    },
    loadData: function(data){

        var project = HOME_PAGE.refData.project;
        var product = HOME_PAGE.refData.product;
        var repository = HOME_PAGE.refData.repository;

        this.data[project][product][repository] = this.data[project][product][repository].concat(data['data']);

        if(this.sliders[project] === undefined){

            this.view.setSliderEl(project, this.sliders);

            //Initialize slider
            var maxDate = 0;
            var minDate = 0;

            var dates = this.getMinMaxDate(data, project, product, repository);

            this.sliders[project]['min'] = parseInt(dates.min);
            this.sliders[project]['max'] = parseInt(dates.max);

            var sliderSel = '#' + this.sliders[project]['id'];

            this.sliders[project]['el'] = $(sliderSel).dateRangeSlider({
                'arrows':true,
                'bounds': {
                    min: new Date(parseInt(data['min_date_data_received']*1000)),
                    max: new Date(this.sliders[project]['max']),
                    },
                'defaultValues': {
                    min: new Date(this.sliders[project]['min']),
                    max: new Date(this.sliders[project]['max'])
                    }
                });

        }else {
            this.view.setSliderEl(project, this.sliders);
        }

        this.getTimeSlice();

        $(this.view.hpContainerSel).trigger(
            this.sliderSliceEvent,
            { 'machine_graph':this.machineGraph,
              'test_graph':this.testGraph,
              'platform_graph':this.platformGraph,
              'graph_size':this.graphSize,
              'slider_min':this.sliders[project]['min'],
              'slider_max':this.sliders[project]['max'] }
            );
    },
    getMinMaxDate: function(data, project, product, repository){

        var dates = { 'min':0, 'max':0 };

        if(this.data[project][product][repository].length > 0){

            dates['max'] = this.data[project][product][repository][0].dr*1000;
            minIndex = this.data[project][product][repository].length - 1;
            dates['min'] = this.data[project][product][repository][minIndex].dr*1000;

        }else{

            dates['max'] = data['min_date_data_received']*1000;
            dates['min'] = data['start']*1000;
        }

        return dates;
    },
    getInternalDataObject: function(obj){
        return jQuery.parseJSON( obj.replace(/'/g, '"') );
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
        this.sliderIdBase = 'slider';
        this.tabSel = '#hp_tabs';

        this.projectSel = '#hp_project';
        this.productRepositorySel = '#hp_repository';
        this.archSel = '#hp_arch';
        this.machinesSel = '#hp_machines';

        $(this.tabSel).tabs();

    },
    setSelectMenu: function(selector, selectOptions, optionDefault){

        var keys = this.getAlphabeticalSortKeys(selectOptions);
        var data = "";
        var option = "";

        var value = $(selector).prop('value');

        var i = 0;
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

        var defaultSelection = optionDefault;
        if(!defaultSelection){
            defaultSelection = value;
        }
        $(selector).val(defaultSelection);
    },
    selectDefaultProject: function(){
        $(this.projectSel).val(HOME_PAGE.refData.project);
    },
    setSliderEl: function(project, sliders){

        //Create slider div if it doesn't exist
        var projectSliderSel = '#' + sliders[project].id;

        if( $(projectSliderSel).length === 0 ){
            var div = $(document.createElement('div'));
            $(div).attr('id', sliders[project].id);
            $(this.sliderSel).append(div);
        }

        //Hide all other sliders
        var sliderProject = "";
        var sliderSel = "";
        for(sliderProject in sliders){

            sliderSel = '#' + sliders[sliderProject].id;

            if(sliderProject != project){
                $(sliderSel).css('display', 'none');
            }else{
                $(sliderSel).css('display', 'block');
            }
        }
    }
});
var SliderModel = new Class({

    Extends:Model,

    jQuery:'SliderModel',

    initialize: function(options){

        this.setOptions(options);

        this.parent(options);

    },
    getProductRepositories: function(context, fnSuccess){

        var uri = HOME_PAGE.urlBase +  HOME_PAGE.refData.project + '/refdata/perftest/ref_data/products';

        jQuery.ajax( uri, {
            accepts:'application/json',
            dataType:'json',
            cache:false,
            type:'GET',
            context:context,
            success:fnSuccess,
        });
    },
    getDataAllDimensions: function(project, product, repository, context, fnSuccess, start, stop){

        var uri = HOME_PAGE.urlBase +  project + '/testdata/all_data?';

        uri += 'product=' + product + '&';
        uri += 'branch=' + repository + '&';

        if(start && stop){
            uri += 'start=' + start + '&stop=' + stop;
        }

        jQuery.ajax( uri, {
            accepts:'application/json',
            dataType:'json',
            cache:false,
            type:'GET',
            context:context,
            success:fnSuccess,
        });
    }
});
