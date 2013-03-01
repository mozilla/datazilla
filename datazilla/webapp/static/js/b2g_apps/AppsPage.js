/*******
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this file,
 * You can obtain one at http://mozilla.org/MPL/2.0/.
 * *****/

APPS_PAGE = {};

var AppsPage = new Class( {

    Extends: Page,

    jQuery:'AppsPage',

    initialize: function(selector, options){

        this.parent(options);
        this.revisionLength = 16;

        this.gaiaHrefBase = "https://github.com/mozilla-b2g/gaia/commit/";
        this.geckoHrefBase = "http://git.mozilla.org/?p=releases/gecko.git;a=commit;h=";
        this.buildHrefBase = "https://github.com/mozilla-b2g/platform_build/commit/";
    },

    setRefData: function(){

        APPS_PAGE.refData = {};

        var urlObj = APPS_PAGE.urlObj.data;
        APPS_PAGE.refData.project = urlObj.seg.path[0];

        APPS_PAGE.urlBase = urlObj.attr.base + urlObj.attr.directory;

        APPS_PAGE.defaults = {};
        APPS_PAGE.defaults['branch'] = urlObj.param.query.branch;
        APPS_PAGE.defaults['range'] = urlObj.param.query.range;
        APPS_PAGE.defaults['test'] = urlObj.param.query.test;
        APPS_PAGE.defaults['app'] = urlObj.param.query.app;

        if( urlObj.param.query.app_list != undefined ){

            var appLookup = {};

            _.map(
                urlObj.param.query.app_list.split(','),
                function(app){
                    appLookup[app] = true;
                }
                );

            APPS_PAGE.defaults['app_list'] = appLookup;
        }

        APPS_PAGE.defaults['gaia_rev'] = urlObj.param.query.gaia_rev;
        APPS_PAGE.defaults['gecko_rev'] = urlObj.param.query.gecko_rev;

    },
    getRevisionSlice: function(revision){
        return revision.slice(0, this.revisionLength);
    }

});

$(document).ready(function() {

    APPS_PAGE = new AppsPage();

    APPS_PAGE.setRefData();

    APPS_PAGE.graphControlsComponent = new GraphControlsComponent();
    APPS_PAGE.performanceGraphComponent = new PerformanceGraphComponent();
    APPS_PAGE.replicateGaphComponent = new ReplicateGraphComponent();

});
