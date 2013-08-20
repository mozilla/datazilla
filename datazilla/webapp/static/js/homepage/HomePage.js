/*******
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this file,
 * You can obtain one at http://mozilla.org/MPL/2.0/.
 * *****/

HOME_PAGE = {};

var HomePage = new Class( {

    Extends: Page,

    jQuery:'HomePage',

    initialize: function(selector, options){

        this.parent(options);

    },
    setUrlBase: function(urlObj){

        if(urlObj.attr.directory.search(/\/$/) === -1){
            urlObj.attr.directory += '/';
        }

        this.urlBase = urlObj.attr.base + urlObj.attr.directory;

    }

});

$(document).ready(function() {

    HOME_PAGE = new HomePage();

    var urlObj = jQuery.url(window.location).data;

    HOME_PAGE.setUrlBase(urlObj);
    HOME_PAGE.selectionState = new SelectionState();
    HOME_PAGE.selectionState.setUrlObj(urlObj);

    HOME_PAGE.NavComponent = new NavComponent();
    HOME_PAGE.SliderComponent = new SliderComponent();
    HOME_PAGE.LineGraphComponent = new LineGraphComponent();

});
