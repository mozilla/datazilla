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
        this.crossfilters = {};
        this.timedimension = {};

        this.sliderMin = 0;
        this.sliderMax = 0;

        $(this.view.sliderSel).bind(
            "valuesChanged", _.bind(this.getRange, this)
            );

        $(this.view.hpContainerSel).bind(
            this.sliderSliceEvent,
            function(ev, data){

                var timeSliceData = crossfilter(data.top(Infinity));

                var all = timeSliceData.groupAll();
                var machineNameDimension = timeSliceData.dimension(
                    function(d){
                        return d.mn;
                        }
                    );
                console.log(machineNameDimension);
            }
            );

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

                $(this.view.hpContainerSel).trigger(
                    this.sliderSliceEvent,
                    this.timeDimension.filterRange([this.sliderMin, this.sliderMax])
                    );

            }
        }
    },
    loadData: function(data){

        if( this.data[HOME_PAGE.refData.project] === undefined){
            this.data[HOME_PAGE.refData.project] = [];
        }

        this.data[HOME_PAGE.refData.project] = this.data[HOME_PAGE.refData.project].concat(data['data']);

        if(!this.slider){

            this.slider = $(this.view.sliderSel).dateRangeSlider({
                'arrows':false,
                'bounds': {
                    min: new Date(parseInt(data['min_date_data_received'])*1000),
                    max: new Date(parseInt(data['max_date_data_received'])*1000),
                    },
                'defaultValues': {
                    min: new Date(parseInt(data['start'])*1000),
                    max: new Date(parseInt(data['stop'])*1000),
                    }
                });

        }

        if(!this.crossfilters[HOME_PAGE.refData.project]){
            //set crossfilter
            this.crossfilters[HOME_PAGE.refData.project] = crossfilter(data['data']);

            this.timeDimension = this.crossfilters[HOME_PAGE.refData.project].dimension(
                        function(d){ return d.dr; }
                );

        }else{
            this.crossfilters[HOME_PAGE.refData.project].add(data['data']);
        }

        $(this.view.hpContainerSel).trigger(
            this.sliderSliceEvent,
            this.timeDimension.filterRange([this.sliderMin, this.sliderMax])
            );
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
        this.tabSel = '#hp-tabs';

        $(this.tabSel).tabs();

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
