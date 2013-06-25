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

        this.view = new NavView();
        this.model = new NavModel();

        this.sliderSliceEvent = 'SLIDER_SLICE_EV';

        $(this.view.hpContainerSel).bind(
            this.sliderSliceEvent, _.bind(this.loadLists, this)
            );

    },
    loadLists: function(ev, data){
        this.view.setList(this.view.testMenuSel, data.data.tests);
        this.view.setList(this.view.platformMenuSel, data.data.platforms);
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

        this.navClickEvent = 'NAV_CLICK_EV';

        this.menuTextLimit = 18;
    },
    setList: function(selector, data){

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
                    this.nodeClick,
                    this,
                    { 'nav':listOrder[i] + '->' + datasetOneSortOrder[j],
                      'data':data[listOrder[i]][datasetOneSortOrder[j]] }));

                $(nestedLi).append(nestedA);
                $(ul).append(nestedLi);
            }

            $(ulRoot).append(li);
        }

        $(selector).append(ulRoot);

        $(ulRoot).menu();
    },
    nodeClick: function(data){

        this.setNav(data.nav);
console.log(data);
        //$(this.hpContainerSel).trigger(this.navClickEvent, data);

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

    }
});
