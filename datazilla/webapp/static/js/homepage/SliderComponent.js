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
         web services. This attribute to name key is stored in
         this.columnKey and is retrieved dynamically.

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

        this.columnKey = {};
        this.sliders = {};
        this.data = {};
        this.productRepositories = {};
        this.selectedData = {};
        this.arch = {};
        this.machines = {};

        var projectData = HOME_PAGE.selectionState.getSelectedProjectData();
        if(projectData.compare_color != ""){
            this.view.setCompareSeriesColor(projectData.compare_color);
        }

        $('.cp-basic').colorpicker(
            {
                'altField': '.cp-basic-target',
                'altProperties': 'background-color,color',

                'buttonClass': 'hp-colorpicker-button',

                'closeOnOutside': true,
                'okOnEnter':true,

                'close': _.bind( function(){

                    var projectData = HOME_PAGE.selectionState.getSelectedProjectData();

                    var color = this.view.getCompareSeriesColor();

                    HOME_PAGE.selectionState.setCompareColor(
                        projectData.project, color.replace('#', '')
                        );

                    HOME_PAGE.LineGraphComponent.view.hideGraphs();
                    HOME_PAGE.LineGraphComponent.view.loadPerformanceGraphs(
                        {}, {});

                    }, this )
            });
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

        this.view.setProject(projectData.project);

        this.setProjectOption(projectData);

    },
    changeProject: function(project){

        $(this.view.projectSel).val(project);
        $(this.view.projectSel).trigger('change');

    },
    changeProductRepository: function(product, repository){

        var productRepository = this.getProductRepositoryString(
            product, repository
            );

        $(this.view.productRepositorySel).val(productRepository);
        $(this.view.productRepositorySel).trigger('change');
    },
    changeSlider: function(project, start, stop){

        $(this.sliders[project].el).dateRangeSlider(
            "values", parseInt(start*1000), parseInt(stop*1000)
            );

    },
    initializeSlider: function(data){

        if(_.isEmpty(this.columnKey)){
            this.columnKey = data.column_key;
        }

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

        var defaultValues = this.getDefaultMinMaxValues(
            project, projectData);

        //Initialize slider
        this.sliders[project].el = $(sliderSel).dateRangeSlider({
            'arrows':false,
            'bounds': {
                min: new Date(parseInt(data['min_date_data_received']*1000)),
                max: new Date(this.sliders[project].max),
                },
            'defaultValues': {
                min: defaultValues.min,
                max: defaultValues.max
                }
            });

        //Initialize to 0 here to trigger data retrieval when the
        //slider initializes
        this.data[project][product][repository]['min'] = 0;
        this.data[project][product][repository]['max'] = 0;

    },
    getDefaultMinMaxValues: function(project, projectData){

        var min = parseInt(projectData.start*1000) || this.sliders[project].min;
        var max = parseInt(projectData.stop*1000) || this.sliders[project].max;

        return { 'min': new Date(min), 'max': new Date(max) };

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


        var project = this.view.getProject();
        var projectData = HOME_PAGE.selectionState.getProjectData(project);

        //First time loading data
        if(this.productRepositories[project] === undefined){

            var productRepository = "";
            var product = "";
            var repository = "";

            this.productRepositories[project] = {};

            var id = 0;
            for(id in data){

                if(data.hasOwnProperty(id)){
                    //Some data is corrupted in production with the
                    //string 'undefined' or an empty string.
                    //Exclude this data.
                    if( (data[id]['product'] === 'undefined') ||
                        (data[id]['branch'] === 'undefined') ||
                        (data[id]['product'] === '') ||
                        (data[id]['branch'] === '') ){

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

        this.view.setSelectMenu(
            this.view.compareProductRepositorySel, this.productRepositories[project],
            this.getProductRepositoryString(
                projectData.product, projectData.repository)
            );

        this.view.addDefaultCompareOption();

        //Initialize the compare series to appropriate state
        HOME_PAGE.NavComponent.view.initializeCompareSeries();

        this.view.setSliderEl(project, this.sliders);
    },
    loadPlatformsAndTests: function(data){

        var project = this.view.getProject();
        var projectData = HOME_PAGE.selectionState.getProjectData(project);
        var product = projectData.product;
        var repository = projectData.repository;

        if(product === "" || repository === ""){
            var prData = this.view.getProductRepository();
            product = prData.product;
            repository = prData.repository;
        }

        var values = {};

        //Initialize the slider
        this.view.setSliderEl(project, this.sliders);

        values = this.getSliderValues(project, projectData);
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

        HOME_PAGE.selectionState.setStart(project, parseInt(values.min/1000));
        HOME_PAGE.selectionState.setStop(project, parseInt(values.max/1000));

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
                this.data[project][product][repository]['platforms'][platform][obj.tn] = { 'os':obj.osn, 'version':obj.osv, 'data':[] };
            }
        }
        //Load test pages
        if(obj.pu != 'undefined'){
            if(this.data[project][product][repository]['tests'][obj.tn][obj.pu] === undefined){
                this.data[project][product][repository]['tests'][obj.tn][obj.pu] = [];
            }
        }
    },
    setProductRepositoryOption: function(){

        HOME_PAGE.NavComponent.view.hideDataContainer();

        var project = this.view.getProject();
        var prData = this.view.getProductRepository();

        HOME_PAGE.selectionState.setProduct(project, prData.product);
        HOME_PAGE.selectionState.setRepository(project, prData.repository);

        this.getPlatformsAndTests();

    },
    getPlatformsAndTests: function(){

        HOME_PAGE.LineGraphComponent.view.hideGraphs();

        var project = this.view.getProject();
        var projectData = HOME_PAGE.selectionState.getProjectData(project);

        var product = projectData.product;
        var repository = projectData.repository;

        if(product === "" || repository === ""){
            var prData = this.view.getProductRepository();
            product = prData.product;
            repository = prData.repository;
        }
        //Get the start and stop time from the slider to
        var values = this.getSliderValues(project, projectData);

        if( (values.min === 0 && values.max === 0) ||
            (values.min < this.data[project][product][repository]['min']) ||
            (values.max > this.data[project][product][repository]['max']) ){

            //Retrieve data from server
            this.model.getPlatformsAndTests(
                project, product, repository, this,
                this.loadPlatformsAndTests,
                this.view.requestError,
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
    getSliderValues: function(project, projectData){

        var values = { 'min':0, 'max':0 };

        if(this.sliders[project].el != undefined){

            var dates = this.sliders[project].el.dateRangeSlider('values');
            values.min = parseInt( dates.min.getTime() );
            values.max = parseInt( dates.max.getTime() );

        }

        return values;
    },
    setProjectOption: function(){

        HOME_PAGE.NavComponent.view.hideDataContainer();

        var project = this.view.getProject();

        HOME_PAGE.selectionState.setProject(project);

        if(this.productRepositories[project] != undefined){
            //Already have the data, load it
            this.loadProductRepositories({});
            this.loadPlatformsAndTests({});

        }else {

            //Retrieve the date range to initialize the slider with
            this.model.getDateRange(
                this, project, _.bind(this.initializeSlider, this),
                _.bind(this.view.requestError, this)
                );

            //Retrieve the product/Repositories associated with the project
            this.model.getProductRepositories(
                this, project, _.bind(this.loadProductRepositories, this),
                _.bind(this.view.requestError, this)
                );

        }
    },
    resizeSlider: function(){
        var project = this.view.getProject();
        this.view.resizeSlider(project, this.sliders[project].id);
    },
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
        this.compareProductRepositorySel = '#hp_compare_options';
        this.archSel = '#hp_arch';
        this.machinesSel = '#hp_machines';
        this.compareSeriesColorSel = '#hp_compare_series_color';

        this.noProductRepositoryOptionValue = 'No Product/Repository selected';

        this.uiTabsClassSel = '.ui-tabs-nav';
        this.graphContainerControlsClassSel = '.hp-graph-container-controls';

        $(this.tabSel).tabs();

        //Insert the graph container control div into the tabs container
        //by the tabs() function call
        $(this.graphContainerControlsClassSel).appendTo(
            $(this.uiTabsClassSel) );

        $(this.graphContainerControlsClassSel).css('display', 'block');
    },
    getCompareSeriesColor: function(){
        return $(this.compareSeriesColorSel).val();
    },
    setCompareSeriesColor: function(color){
        return $(this.compareSeriesColorSel).val(color);
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
    },
    resizeSlider: function(project, sliderId){
        var sliderSel = '#' + sliderId;
        $(sliderSel).resize();
    },
    addDefaultCompareOption: function(){
        var option = $('<option></option>');
        $(option).text( this.noProductRepositoryOptionValue );
        $(this.compareProductRepositorySel).prepend(option);
        $(this.compareProductRepositorySel).val(option);
    }
});
var SliderModel = new Class({

    Extends:Model,

    jQuery:'SliderModel',

    initialize: function(options){

        this.setOptions(options);

        this.parent(options);

    },
    getDateRange: function(context, project, fnSuccess, fnError){

        var uri = HOME_PAGE.urlBase +  project + '/testdata/all_data_date_range';

        jQuery.ajax( uri, {
            accepts:'application/json',
            dataType:'json',
            cache:false,
            type:'GET',
            context:context,
            success:fnSuccess,
            timeout:40000,
            error:fnError
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
    getPlatformsAndTests: function(
        project, product, repository, context, fnSuccess, fnError, start, stop){

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
            error:fnError
        });

    }
});
