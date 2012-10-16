/*******
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this file,
 * You can obtain one at http://mozilla.org/MPL/2.0/.
 * *****/

MS_PAGE = {};

var MetricSummaryPage = new Class( {

    Extends: Page,

    jQuery:'MetricSummaryPage',

    initialize: function(selector, options){

        this.parent(options);

        this.failColor = '#FF7700';
        this.passColor = '#44AA00';
    },

    setRefData: function(){

        MS_PAGE.refData = {};

        MS_PAGE.refData.project = MS_PAGE.urlObj.data.seg.path[0];
        MS_PAGE.refData.branch = MS_PAGE.urlObj.data.seg.path[2];
        MS_PAGE.refData.revision = MS_PAGE.urlObj.data.seg.path[3];
    }

});

$(document).ready(function() {

    MS_PAGE = new MetricSummaryPage();

    MS_PAGE.setRefData();

    MS_PAGE.trendLineComponent = new TrendLineComponent();
    MS_PAGE.testPagesComponent = new TestPagesComponent();
    MS_PAGE.metricGridComponent = new MetricGridComponent();
    MS_PAGE.metricDashboardComponent = new MetricDashboardComponent();

});
