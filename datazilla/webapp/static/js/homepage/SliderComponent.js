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


         this.data[project][product][repository] =
            { min:
              max:
              data: [ ] }

        *******************/
        this.setOptions(options);

        this.parent(options);

        this.view = new SliderView();
        this.model = new SliderModel();

        this.sliderSliceEvent = 'SLIDER_SLICE_EV';

        this.sliders = {};
        this.data = {};
        this.productRepositories = {};
        this.selectedData = {};
        this.arch = {};
        this.machines = {};

        //User selects a project
        $(this.view.projectSel).bind(
            "change", _.bind(this.setProjectOption, this)
            );

        //User selects a product/repository
        $(this.view.productRepositorySel).bind(
            "change", _.bind(this.setProductRepositoryOption, this)
            );

        //This is triggered the first time the slider
        //initializes and when a user drags the date
        //controls.
        $(this.view.sliderSel).bind(
            "valuesChanged", _.bind(this.getPlatformsAndTests, this)
            );

        var projectData = HOME_PAGE.selectionState.getSelectedProjectData();
        this.view.setProject(projectData.project);

        this.setProjectOption(projectData);

    },
    initializeSlider: function(data){

        var project = this.view.getProject();
        var projectData = HOME_PAGE.selectionState.getProjectData(project);

        var product = projectData.product;
        var repository = projectData.repository;

        this.initializeProjectData(project, product, repository);

        this.sliders[project] = {
            'el':undefined, 'id':this.view.sliderIdBase + '_' + project,
            'min':0, 'max':0
        };

        this.view.setSliderEl(project, this.sliders);

        var dates = this.getMinMaxDate(data, project, product, repository);

        this.sliders[project].min = parseInt(dates.min);
        this.sliders[project].max = parseInt(dates.max);

        var sliderSel = '#' + this.sliders[project].id;

        //Initialize slider
        this.sliders[project].el = $(sliderSel).dateRangeSlider({
            'arrows':false,
            'bounds': {
                min: new Date(parseInt(data['min_date_data_received']*1000)),
                max: new Date(this.sliders[project].max),
                },
            'defaultValues': {
                min: new Date(this.sliders[project].min),
                max: new Date(this.sliders[project].max)
                }
            });

        //Initialize to 0 here to trigger data retrieval when the
        //slider initializes
        this.data[project][product][repository]['min'] = 0;
        this.data[project][product][repository]['max'] = 0;

    },
    initializeProjectData: function(project, product, repository){

        if(this.data[project] === undefined){
            this.data[project] = {};
        }

        if(this.data[project][product] === undefined){
            this.data[project][product] = {};
        }

        if(this.data[project][product][repository] === undefined){
            this.data[project][product][repository] = {
                'min':0, 'max':0, 'tests':{}, 'platforms':{}
                };
         }
    },
    loadProductRepositories: function(data){

        var id = 0;

        var project = this.view.getProject();
        var projectData = HOME_PAGE.selectionState.getProjectData(project);

        //First time loading data
        if(this.productRepositories[project] === undefined){

            var productRepository = "";
            var product = "";
            var repository = "";

            this.productRepositories[project] = {};

            for(id in data){

                if(data.hasOwnProperty(id)){
                    //Some data is corrupted in production with the
                    //string 'undefined'. Exclude this data.
                    if( (data[id]['product'] === 'undefined') ||
                        (data[id]['branch'] === 'undefined') ){

                        continue;
                    }

                    productRepository = data[id]['product'] + ' ' + data[id]['branch'];

                    repository = data[id]['branch'];
                    product = data[id]['product'];

                    if(this.productRepositories[project][productRepository] === undefined){
                        this.productRepositories[project][productRepository] = {
                            'b':repository, 'p':product
                            };
                    }

                    this.initializeProjectData(project, product, repository);
                }
            }
        }

        this.view.setSelectMenu(
            this.view.productRepositorySel, this.productRepositories[project],
            this.getProductRepositoryString(
                projectData.product, projectData.repository)
            );

        this.view.setSliderEl(project, this.sliders);
    },
    loadPlatformsAndTests: function(data){

        var project = this.view.getProject();
        var projectData = HOME_PAGE.selectionState.getProjectData(project);
        var product = projectData.product;
        var repository = projectData.repository;

        var values = {};

        //Initialize the slider
        this.view.setSliderEl(project, this.sliders);

        values = this.getSliderValues(project);

        if( (values.min < this.data[project][product][repository]['min']) ||
            (this.data[project][product][repository]['min'] === 0) ){

            this.data[project][product][repository]['min'] = values.min;

        }
        if(values.max > this.data[project][product][repository]['max']){

            this.data[project][product][repository]['max'] = values.max;

        }

        _.map(
            data.data,
            _.bind(
                this.aggregateTestsAndPages, this, project, product,
                repository )
            );

        $(this.view.hpContainerSel).trigger(
            this.sliderSliceEvent,
            { 'project':project,
              'product':product,
              'repository':repository,
              'data':this.data[project][product][repository],
              'slider_min':values.min,
              'slider_max':values.max }
            );
    },
    aggregateTestsAndPages: function(project, product, repository, obj){

        var platform = obj.osn + ' ' + obj.osv;

        //Load platforms
        if(this.data[project][product][repository]['platforms'][platform] === undefined){
            this.data[project][product][repository]['platforms'][platform] = {};
        }

        //Load tests
        if(obj.tn != 'undefined'){
            if(this.data[project][product][repository]['tests'][obj.tn] === undefined){
                this.data[project][product][repository]['tests'][obj.tn] = {};
            }
            if(this.data[project][product][repository]['platforms'][platform][obj.tn] === undefined){
                this.data[project][product][repository]['platforms'][platform][obj.tn] = [];
            }
        }
        //Load test pages
        if(obj.pu != 'undefined'){
            if(this.data[project][product][repository]['tests'][obj.tn][obj.pu] === undefined){
                this.data[project][product][repository]['tests'][obj.tn][obj.pu] = [];
            }
        }
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
    setProductRepositoryOption: function(){

        var project = this.view.getProject();
        var prData = this.view.getProductRepository();

        HOME_PAGE.selectionState.setProduct(project, prData.product);
        HOME_PAGE.selectionState.setRepository(project, prData.repository);

        this.getPlatformsAndTests();

    },
    getPlatformsAndTests: function(){

        var project = this.view.getProject();

        var projectData = HOME_PAGE.selectionState.getProjectData(project);

        var product = projectData.product;
        var repository = projectData.repository;

        //Get the start and stop time from the slider to
        var values = this.getSliderValues(project);

        if( (values.min === 0 && values.max === 0) ||
            (values.min < this.data[project][product][repository]['min']) ||
            (values.max > this.data[project][product][repository]['max']) ){

            //Retrieve data from server
            this.model.getPlatformsAndTests(
                project, product, repository, this,
                this.loadPlatformsAndTests,
                parseInt(values.min/1000), parseInt(values.max/1000)
                );

        }else {
            //Data has already been retrieved, load it
            this.loadPlatformsAndTests({});
        }

    },
    getProductRepositoryString: function(product, repository){
        return product + ' ' + repository;
    },
    getMinMaxDate: function(data, project, product, repository){

        var dates = { 'min':0, 'max':0 };

        dates['max'] = data['max_date_data_received']*1000;
        dates['min'] = data['start']*1000;

        return dates;
    },
    getSliderValues: function(project){

        var values = { 'min':0, 'max':0 };

        if(this.sliders[project].el != undefined){

            var dates = this.sliders[project].el.dateRangeSlider('values');
            values.min = parseInt( dates.min.getTime() );
            values.max = parseInt( dates.max.getTime() );

        }

        return values;
    },
    setProjectOption: function(){

        var project = this.view.getProject();

        HOME_PAGE.selectionState.setProject(project);

        if(this.productRepositories[project] != undefined){
            //Already have the data, load it
            this.loadProductRepositories({});
            this.loadPlatformsAndTests({});

        }else {
            //Retrieve data
            this.model.getDateRange(
                this, project, _.bind(this.initializeSlider, this)
                );

            this.model.getProductRepositories(
                this, project, _.bind(this.loadProductRepositories, this)
                );

        }
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
    setSliderEl: function(project, sliders){

        //Create slider div if it doesn't exist
        if(sliders[project] != undefined){

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
                    $(sliderSel).resize();
                }
            }
        }
    },
    getProject: function(){
        return $(this.projectSel).find(":selected").val() || HOME_PAGE.selectionState.defaultProject;
    },
    setProject: function(project){
        $(this.projectSel).val(project || HOME_PAGE.selectionState.defaultProject);
    },
    getProductRepository: function(){

        var selectedOption = $(this.productRepositorySel).find(":selected");

        var data = {
            'product':"",
            'repository':""
            };

        if(selectedOption.length > 0){

            var optDataStr = $(selectedOption).attr('internal_data');
            optData = this.getInternalDataObject(optDataStr);
            data.product = optData.p;
            data.repository = optData.b;

        }

        return data;
    },
    getInternalDataObject: function(obj){
        return jQuery.parseJSON( obj.replace(/'/g, '"') );
    }
});
var SliderModel = new Class({

    Extends:Model,

    jQuery:'SliderModel',

    initialize: function(options){

        this.setOptions(options);

        this.parent(options);

    },
    getDateRange: function(context, project, fnSuccess){

        var uri = HOME_PAGE.urlBase +  project + '/testdata/all_data_date_range';

        jQuery.ajax( uri, {
            accepts:'application/json',
            dataType:'json',
            cache:false,
            type:'GET',
            context:context,
            success:fnSuccess,
        });

    },
    getProductRepositories: function(context, project, fnSuccess){

        var uri = HOME_PAGE.urlBase +  project + '/refdata/perftest/ref_data/products';

        jQuery.ajax( uri, {
            accepts:'application/json',
            dataType:'json',
            cache:false,
            type:'GET',
            context:context,
            success:fnSuccess,
        });
    },
    getPlatformsAndTests: function(project, product, repository, context, fnSuccess, start, stop){

        var uri = HOME_PAGE.urlBase +  project + '/testdata/platforms_tests?';

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

    },
    getDataAllDimensions: function(project, product, repository, context, fnSuccess, start, stop){

        var uri = HOME_PAGE.urlBase +  project + '/testdata/all_data?';

        uri += 'product=' + product + '&';
        uri += 'branch=' + repository + '&';
        uri += 'test=' + repository + '&';

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
