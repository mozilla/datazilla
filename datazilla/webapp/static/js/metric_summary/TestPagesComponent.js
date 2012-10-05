/*******
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this file,
 * You can obtain one at http://mozilla.org/MPL/2.0/.
 * *****/
var TestPagesComponent = new Class({

    Extends: Component,

    jQuery:'TestPagesComponent',

    initialize: function(selector, options){

        this.setOptions(options);

        this.parent(options);

        this.view = new TestPagesView('#TestPagesView',{});
        this.model = new TestPagesModel('#TestPagesModel',{});

    },
    initializeTestPages: function(ev, data){

        if(_.isEmpty(data)){

        }else{
            this.view.initializeTestPages(data);
        }
    }
});
var TestPagesView = new Class({

    Extends:View,

    jQuery:'TestPagesView',

    initialize: function(selector, options){

        this.setOptions(options);

        this.parent(options);

        this.eventContainerSel = '#su_container';
        this.barChartContainerSel = '#su_test_pages';

        this.gridClickEvent = 'GRID_CLICK_EVENT';
        this.gridMouseoverEvent = 'GRID_MOUSEOVER_EVENT';

        $(this.eventContainerSel).bind(
            this.gridMouseoverEvent,
            _.bind(this.initializeTestPages, this)
        );

    },

    initializeTestPages: function(event, data){

        console.log(data);

        //var columns = this.getAlphabeticalSortKeys(
         //   data.summary_by_platform
          //  );

    },
    _updatePlot: function(data){

        if(this.plot){
            this.plot.shutdown();
            $(this.barChartContainerSel).unbind('plotclick');
            $(this.barChartContainerSel).unbind('plothover');
        }
        this.plot = $.plot(
            $(this.barChartContainerSel), data, this.plotOptions
            );

        this.barChartContainerSel = '#su_test_pages';

        this._setYaxisLabel(this.yAxisLabel);

        $(this.barChartContainerSel).bind(
            'plotclick', _.bind(this._clickPlot, this)
            );
        $(this.barChartContainerSel).bind(
            'plothover', _.bind(this._hoverPlot, this)
            );
    },
    _setYaxisLabel: function(label){
        /*
        var labelEl = $('<div class="css-left dv-verticaltext" style="position:absolute;' + 
                             ' top:235px; right:' + this.width + 'px;">' + label + '</div>');
        var yaxisLabelContainer = $(this.selectors.graph_container).find(this.flotLabelClassSel);

        $(yaxisLabelContainer).append(labelEl);
        */
    },
});

var TestPagesModel = new Class({

    Extends:Model,

    jQuery:'TestPagesModel',

    initialize: function(options){

        this.setOptions(options);

        this.parent(options);

    }
});
