/*******
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this file,
 * You can obtain one at http://mozilla.org/MPL/2.0/.
 * *****/
var MetricGaugeComponent = new Class({

    Extends: Component,

    jQuery:'MetricGaugeComponent',

    initialize: function(selector, options){

        this.setOptions(options);

        this.parent(options);

        this.view = new MetricGaugeView('#MetricGaugeView',{});
        this.model = new MetricGaugeModel('#MetricGaugeModel',{});

        this.model.getMetricSummary(
            this, this.initializeGauge, this.dataLoadError
            );
    },
    initializeGauge: function(data){

        console.log('data');
        console.log(data);

        this.view.initializeGauge(data);
    },
    dataLoadError: function(data, textStatus, jqXHR){

        var messageText = 'Ohhh no, something has gone horribly wrong! ';

        messageText += ' HTTP status:' + data.status + ', ' + textStatus +
        ', ' + data.statusText;

        console.log(messageText);

    }

});
var MetricGaugeView = new Class({

    Extends:View,

    jQuery:'MetricGaugeView',

    initialize: function(selector, options){

        this.setOptions(options);

        this.parent(options);

        this.mainGaugeId = 'su_gauge_1';

        this.summaryByTestContainer = '#su_summary_by_test';
        this.summaryByPlatformContainer = '#su_summary_by_platform';

        this.progressBarContainerSel = '#su_progressbar_container';
        this.progressBarTitleSel = '#su_progressbar_title';
        this.progressBarSel = '#su_progressbar';
        this.progressBarTitleClassName = 'su-progressbar-title';
        this.progressBarClassName = 'su-progressbar';

        this.failColor = '#FF7700';
        this.passColor = '#44AA00';

    },

    initializeGauge: function(data){

        //Initialize main gauge
        this.mainGauge = new JustGage({

            id: this.mainGaugeId,
            value: data.summary.pass.percent,
            width: 250,
            min: 0,
            max: 100,
            title: "Talos Summary",
            label: "Percent Pass",

            showInnerShadow: true,
            levelColorsGradient: true,

            gaugeColor: this.failColor,
            levelColors: [this.passColor]
        });

        this.loadProgressBars(
            this.summaryByTestContainer, data.summary_by_test
            );

        this.loadProgressBars(
            this.summaryByPlatformContainer, data.summary_by_platform
            );

    },
    loadProgressBars: function(targetContainer, data){

        pbContainer = $(this.progressBarContainerSel).clone();

        $(pbContainer).attr('id', "");
        $(pbContainer).css('width', 275);

        for (title in data){
            if (data.hasOwnProperty(title)){

                container = $('<div></div>');
                $(container).css('margin-bottom', 10);

                titleDiv = $('<div>' + title + '</div>');
                titleDiv.addClass(this.progressBarTitleClassName);

                $(container).append(titleDiv);

                pb = $('<div></div>').clone();
                $(pb).addClass(this.progressBarClassName);

                percent = data[title].pass.percent;

                $(pb).progressbar({
                    value: percent
                });

                $(container).append(pb);


                valueDiv = $('<div>' + percent + '%</div>');
                $(valueDiv).css('float', 'right');
                $(valueDiv).css('margin-bottom', 5);
                $(valueDiv).css('margin-left', 5);
                $(container).append(valueDiv);

                $(pbContainer).append(container);

                $(targetContainer).append(pbContainer);
            }
        }
        //The inner div in the progress bar gives
        //the "bar" foreground appearance, collor it
        //by the pass color
        $('.' + this.progressBarClassName + ' > div').css(
            'background', this.passColor
            );
    }
});
var MetricGaugeModel = new Class({

    Extends:Model,

    jQuery:'MetricGaugeModel',

    initialize: function(options){

        this.setOptions(options);

        this.parent(options);

    },

    getMetricSummary: function(context, fnSuccess, fnError){

        uri = '/' + MS_PAGE.refData.project +
            '/testdata/metrics/' + MS_PAGE.refData.branch +
            '/' + MS_PAGE.refData.revision + '/summary';

        console.log(uri);

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
