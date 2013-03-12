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
        this.branchUri = '/refdata/pushlog/branch_uri?branch=';
        this.revisionUrl = 'https://hg.mozilla.org/URI/pushloghtml?TYPE=';
        this.bugzillaUrl = 'https://bugzilla.mozilla.org/show_bug.cgi?id=';

    },

    getHgUrlATag: function(type, revision){
        /****
         * Get an html <a> tag for the given type and revision provided.
         * Type can be 'rev' or 'changeset'.
         ****/
        var revisionUrl = this.revisionUrl.replace(
            'URI', MS_PAGE.refData.branch_uri
            );

        revisionUrl = revisionUrl.replace(
            'TYPE', type
            ) + revision;

        var a = $(document.createElement('a'));
        $(a).attr('href', revisionUrl);
        $(a).attr('target', '_blank');
        $(a).text(revision);

        return a;
    },
    addBugzillaATagsToDesc: function(desc){
        /****
         * Replace bugzilla bug number strings (Bug 123456) with
         * an html <a> tag.
         ****/
        return desc.replace(
            /(bug).*?(\d+)/ig,
            '<a target="_blank" href="' + this.bugzillaUrl + "$2" +
            '">$1 $2</a>');
    },
    setRefData: function(){

        MS_PAGE.refData = {};

        var urlObj = MS_PAGE.urlObj.data;

        MS_PAGE.urlObj = urlObj;
        MS_PAGE.refData.project = urlObj.seg.path[0];
        MS_PAGE.refData.branch = urlObj.seg.path[2];
        MS_PAGE.refData.revision = urlObj.seg.path[3];
        MS_PAGE.refData.product = urlObj.param.query.product;
        MS_PAGE.refData.branch_version = urlObj.param.query.branch_version;
        MS_PAGE.refData.test = urlObj.param.query.test;
        MS_PAGE.refData.platform = urlObj.param.query.platform;

    },
    getDatumKey: function(data){
        /***
         * Build a unique datum string and convert to a hash
         ***/
        var key = data.platform_info.operating_system_name +
            data.platform_info.operating_system_version +
            data.platform_info.processor +
            data.platform_info.type +
            data.testsuite +
            data.pagename;

        key = key.hashCode();

        return key;
    },
    getBranchUri: function(){

        var url = this.branchUri + MS_PAGE.refData.branch;
        jQuery.ajax( url, {
            accepts:'application/json',
            dataType:'json',
            cache:false,
            type:'GET',
            context:this,
            success: function(data, textStatus, jqXHR){
                MS_PAGE.refData.branch_uri = data[0].uri;
                }
            });
    }

});

$(document).ready(function() {

    MS_PAGE = new MetricSummaryPage();

    MS_PAGE.setRefData();
    MS_PAGE.getBranchUri();

    //Commenting out until we cache the data
    //MS_PAGE.trendLineComponent = new TrendLineComponent();
    MS_PAGE.testPagesComponent = new TestPagesComponent();
    MS_PAGE.metricGridComponent = new MetricGridComponent();
    MS_PAGE.metricDashboardComponent = new MetricDashboardComponent();

});
