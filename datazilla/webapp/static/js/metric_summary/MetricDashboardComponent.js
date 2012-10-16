/*******
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this file,
 * You can obtain one at http://mozilla.org/MPL/2.0/.
 * *****/
var MetricDashboardComponent = new Class({

    Extends: Component,

    jQuery:'MetricDashboardComponent',

    initialize: function(selector, options){

        this.setOptions(options);

        this.parent(options);

        this.metricSummaryDataEvent = 'METRIC_SUMMARY_EV';

        this.view = new MetricDashboardView('#MetricDashboardView',{});
        this.model = new MetricDashboardModel('#MetricDashboardModel',{});

        this.model.getMetricSummary(
            this, this.initializeDashboard, this.dataLoadError
            );
    },
    initializeDashboard: function(data){

        //Send data event for any listeners that need
        //to initialize
        $(this.view.eventContainerSel).trigger(
            this.metricSummaryDataEvent, data
            );

        if(_.isEmpty(data)){
            this.view.showNoDataMessage();
        }else{

            this.view.initializeDashboard(data);
        }
    },
    dataLoadError: function(data, textStatus, jqXHR){

        var messageText = 'Ohhh no, something has gone horribly wrong! ';

        messageText += ' HTTP status:' + data.status + ', ' + textStatus +
        ', ' + data.statusText;

    }
});
var MetricDashboardView = new Class({

    Extends:View,

    jQuery:'MetricDashboardView',

    initialize: function(selector, options){

        this.setOptions(options);

        this.parent(options);

        this.progressBars = {};

        this.eventContainerSel = '#su_container';

        this.mainGaugeId = 'su_gauge_1';

        this.spinnerSel = '#su_dashboard_spinner';
        this.noDataSel = '#su_no_data';
        this.noDataMessageSel = '#su_no_data_message';
        this.dashboardSel = '#su_dashboard';

        this.summaryByTestContainerSel = '#su_summary_by_test';
        this.summaryByPlatformContainerSel = '#su_summary_by_platform';

        this.progressBarTitleSel = '#su_progressbar_title';
        this.progressBarSel = '#su_progressbar';
        this.progressBarTitleClassName = 'su-progressbar-title';
        this.progressBarClassName = 'su-progressbar';

        this.productTestsSel = '#su_product_tested';
        this.revisionTestedSel = '#su_revision_tested';
        this.totalCountSel = '#su_total_count';
        this.noTrendCountSel = '#su_no_trend_count';
        this.passCountSel = '#su_pass_count';
        this.failCountSel = '#su_fail_count';

        this.dashboardPanelClass = 'su-dashboard-panel';
        this.referenceInfoPanelClass = 'su-reference-info';

        this.progressbarValueClassSel = '.ui-progressbar-value';


    },

    initializeDashboard: function(data){

        //Initialize main gauge
        this.mainGauge = new JustGage({

            id: this.mainGaugeId,
            value: data.summary.pass.percent,
            min: 0,
            max: 100,
            title: "Talos Dashboard",
            label: "Percent Passed",

            showInnerShadow: true,
            levelColorsGradient: true,

            gaugeColor: MS_PAGE.failColor,
            levelColors: [MS_PAGE.passColor]
        });

        //Initialize progress bars
        this.loadProgressBars(
            this.summaryByTestContainerSel, data.summary_by_test,
            this.getAlphabeticalSortKeys(data.summary_by_test)
            );

        this.loadProgressBars(
            this.summaryByPlatformContainerSel, data.summary_by_platform,
            this.getAlphabeticalSortKeys(data.summary_by_platform)
            );

        //Set reference info
        this.setReferenceInfo(data);

        this.toggleDashboard(true);

        this.animateProgressBars();
    },
    toggleDashboard: function(toggleOn, target){

        $(this.spinnerSel).hide();

        if (toggleOn){

            $('.' + this.dashboardPanelClass).css('display', 'block');

            $(this.dashboardSel).show();
            $('.' + this.referenceInfoPanelClass).css('display', 'block');

        } else {

            $('.' + this.dashboardPanelClass).css('display', 'none');

            $(this.dashboardSel).hide();
            $('.' + this.referenceInfoPanelClass).css('display', 'none');

            if (target){
                $(target).show();
            }
        }
    },
    showNoDataMessage: function(){

        var message = MS_PAGE.refData.revision + ' ' +
            MS_PAGE.refData.branch;

        $(this.noDataMessageSel).text(message);

        this.toggleDashboard(false, this.noDataSel);

    },
    animateProgressBars: function(){
        for(var title in this.progressBars){

            var percent = this.progressBars[title]['value'];

            //Get the parent element width
            var parentWidth = parseInt(
                $(this.progressBars[title]['pb']).css('width')
                );

            //Calculate the percent width
            var width = Math.floor( (parseInt(percent)/100)*parentWidth );

            //Run animation
            var el = $(this.progressBars[title]['pb']).find(
                this.progressbarValueClassSel
                );

            $(el).css('display', 'block');
            $(el).stop().animate(
                {width:width},
                {queue:false, duration:1000}
                );
        }
    },
    setReferenceInfo: function(data){

        var productInfo = data.product_info.name + ' ' +
            data.product_info.branch + ' ' + data.product_info.version;

        $(this.productTestsSel).text(productInfo);

        $(this.revisionTestedSel).text(
            data.product_info.revision
            );

        $(this.noTrendCountSel).text(data.summary.keys_without_trend);
        $(this.totalCountSel).text(data.summary.total_tests);

        $(this.passCountSel).text(data.summary.pass.value + ' passed');
        $(this.failCountSel).text(data.summary.fail.value + ' failed');

    },
    loadProgressBars: function(targetContainer, data, order){

        var pbContainer = $('<div class="su-progressbar-container"></div>');

        var title = "";
        for(var i=0; i<order.length; i++){

            title = order[i];

            if (data.hasOwnProperty(title)){

                container = $('<div></div>');
                $(container).css('margin-bottom', 10);

                titleDiv = $('<div class="su-light-text">' +
                    title + '</div>');

                titleDiv.addClass(this.progressBarTitleClassName);

                $(container).append(titleDiv);

                pb = $('<div></div>').clone();
                $(pb).addClass(this.progressBarClassName);

                percent = data[title].pass.percent;

                $(pb).progressbar();


                this.progressBars[title] = { pb:pb, value:percent };

                $(container).append(pb);

                valueDiv = $('<div class="su-progressbar-value su-light-text">' +
                    percent + '%</div>');

                $(container).append(valueDiv);

                $(pbContainer).append(container);

                $(targetContainer).append(pbContainer);
            }
        }
        //The inner div in the progress bar gives
        //the "bar" foreground appearance, color it
        //by the pass color
        $('.' + this.progressBarClassName + ' > div').css(
            'background', MS_PAGE.passColor
            );

        $('.' + this.progressBarClassName + ' > div').addClass(
            this.progressbarValueClassSel
            );
    }
});
var MetricDashboardModel = new Class({

    Extends:Model,

    jQuery:'MetricDashboardModel',

    initialize: function(options){

        this.setOptions(options);

        this.parent(options);

    },

    getMetricSummary: function(context, fnSuccess, fnError){

        uri = '/' + MS_PAGE.refData.project +
            '/testdata/metrics/' + MS_PAGE.refData.branch +
            '/' + MS_PAGE.refData.revision + '/summary';

        jQuery.ajax( uri, {
            accepts:'application/json',
            dataType:'json',
            cache:false,
            type:'GET',
            data:data,
            context:context,
            error:fnError,
            success:fnSuccess,
        });
    }
});
