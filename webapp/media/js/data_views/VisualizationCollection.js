/******* 
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this file,
 * You can obtain one at http://mozilla.org/MPL/2.0/. 
 * *****/
var VisualizationCollection = new Class({

   Extends:Options,

   jQuery:'VisualizationCollection',

   initialize: function(selector, options){

      this.setOptions(options);

      //Holds a list of adapters.  The key should be found in
      //views.json in the data_adapter attribute.
      this.visualizations = { 'average_thumbnails':new AverageThumbnails(),
                              'test_chart':new ScatterPlot(),
                              'box_plot':new BoxPlot(),
                              'scatter_label_plot':new ScatterLabelPlot(),
                              'side_bars':new SideBarPlot() };

   },

   display: function(displayData, menuToggle){
      if(this.visualizations[displayData.vis_name] != undefined){

         this.visualizations[displayData.vis_name].setSelectors(displayData.selectors);
         this.visualizations[displayData.vis_name].setSignalData(displayData.signal_data);
         this.visualizations[displayData.vis_name].setIncomingSignalData(displayData.incoming_signal_data);
         this.visualizations[displayData.vis_name].display(displayData.data, menuToggle);
      }
   },

   getVisData: function(visName){
      var data = [];
      if((visName != undefined) && (this.visualizations[visName] != undefined)){
         data = this.visualizations[visName].getVisData();
      }
      return data;
   },
   clear: function(visName){
      if((visName != undefined) && (this.visualizations[visName] != undefined)){
         this.visualizations[visName].clear();
      }
   }
});
var Visualization = new Class({

   Extends:Options,

   jQuery:'Visualization',

   initialize: function(options){

      this.setOptions(options);

      this.formatTimestamp = d3.time.format("%Y-%m-%d %H:%M:%S");

      //Selectors for specific dview this Visualization 
      //is operating on
      this.selectors = {};

      //Signal identification data for dview
      this.signalData = {};

      this.allViewsContainerSel = '#dv_view_container';

      this.signalEvent = 'SIGNAL_DATAVIEW';

   },
   setSelectors: function(selectors){
      this.selectors = selectors;
   },
   setSignalData: function(signalData){
      this.signalData = signalData;
   },
   setGraphContainerSize: function(w, h){
      if(w > 0){
         $(this.selectors.graph_container).css('width', w);
         $(this.selectors.graph_detail_two).css('width', w);
      }
      if(h > 0){
         var graphDetailTwoHeight = parseInt($(this.selectors.graph_detail_two).css('height'));

         $(this.selectors.graph_container).css('height', h);
         $(this.selectors.graph_detail).css('height', h + graphDetailTwoHeight);
      }
   },
   setIncomingSignalData: function(incomingSignalData){
      this.incomingSignalData = incomingSignalData;
   },
   clearContainers: function(selectors){
      $(selectors.graph_container).empty();
      $(selectors.graph_detail).empty();
      $(selectors.graph_detail_two).empty();
   },
   getProductName: function(productId){

      var product = "";

      if( DV_PAGE.refData.products[productId] != undefined ){
         product = DV_PAGE.refData.products[productId].product + ' ' +
                   DV_PAGE.refData.products[productId].version + ' ' +
                   DV_PAGE.refData.products[productId].branch;
      }
      return product;

   },
   getProductAndBranch: function(productId){

      var productAndBranch = [];

      if( DV_PAGE.refData.products[productId] != undefined ){
         productAndBranch.push( DV_PAGE.refData.products[productId].product + ' ' +
                                DV_PAGE.refData.products[productId].version );

         productAndBranch.push( DV_PAGE.refData.products[productId].branch );
      }

      return productAndBranch;

   },
   getTestName: function(testId){
      var testName = "";
      if( DV_PAGE.refData.tests[testId] != undefined ){
         testName = DV_PAGE.refData.tests[testId].name;
      }
      return testName;
   },
   getOsName: function(osId){
      var osName = "";
      if( DV_PAGE.refData.operating_systems[osId] != undefined ){

         osName = DV_PAGE.refData.operating_systems[osId].name + ' ' +
                    DV_PAGE.refData.operating_systems[osId].version;
      }
      return osName;
   },
   getRevision: function(revisionHtml){
      return $(revisionHtml).text();
   },
   getDataObjectFromString: function(dataString){

      var dataObject = {};
      if(dataString != undefined){
         var dataFields = dataString.split('&');
         for(var i=0; i<dataFields.length; i++){
            var keyValue = dataFields[i].split('=');
            dataObject[ keyValue[0] ] = keyValue[1];
         }
      }
      return dataObject;
   }
});
var AverageThumbnails = new Class({

   Extends:Visualization,

   jQuery:'DataViewAdapter',

   initialize: function(options){

      this.setOptions(options);
      this.parent(options);

      this.adaptedDataFields = [ 'average',
                                 'min',
                                 'max',
                                 'standard_deviation',
                                 'variance',
                                 'revision',
                                 'date_run',
                                 'readable_date' ];
     
   },
   display: function(data, menuToggle){

      this.clearContainers(this.selectors);

      this._configureGraphContainer();

      var aggregateData = this.adaptData(data);

      //Dimensions of a single tile
      var padding = 5;
      var width = 150;
      var height = 50;

      var osOrder = aggregateData['operating_systems']['order'];

      var containerWidth = parseInt( (900)*(osOrder.length+1)/6 );

      this.setGraphContainerSize(containerWidth);

      for( var productId in aggregateData['data'] ){

         if(aggregateData['data'].hasOwnProperty(productId)){
            var productTile = {};

            for( var i=0; i<osOrder.length; i++){
               //Draw empty tile to maintain alignment
               if(i === 0){
                  productTile = this._drawEmptyTile(padding, width, height);
               }
               var label = aggregateData['operating_systems']['id'][ osOrder[i] ];
               this._drawLabel(label, padding, width, height);
            }
            //Draw the prodcut, version, branch on the label
            var productAndBranch = this.getProductAndBranch(productId);
            this._drawTitleLabel(productTile, productAndBranch, padding, width, height);

            for( var testId in aggregateData['data'][productId] ){

               if(aggregateData['data'][productId].hasOwnProperty(testId)){

                  var testName = this.getTestName(testId);

                  this._drawLabel(testName, padding, width, height);

                  for( var i=0; i<osOrder.length; i++){

                     var osId = osOrder[i];

                     if(aggregateData['data'][productId][testId][osId] === undefined){
                        this._drawEmptyTile(padding, width, height);
                     }else{
                        var data = aggregateData['data'][productId][testId][osId];

                        //REMOVE BEFORE RELEASE: This is for the demo data
                        if(data.average.length <= 5){
                           for(var j=0; j<10; j++){
                              //data.average.push( parseFloat(data.average[0] || 0)+20*Math.random() );
                              //data.standard_deviation.push( parseFloat(data.standard_deviation[0] || 0) + Math.random() );
                              data.average.push( parseFloat(data.average[0] || 0) );
                              data.standard_deviation.push( parseFloat(data.standard_deviation[0] || 0) );
                           }
                        }


                        data['product_id'] = productId;
                        data['test_id'] = testId;
                        data['os_id'] = osId;

                        this._drawTile(data, padding, width, height);
                     }
                  }
               }
            }
         }
      }
   },
   adaptData: function(data){

      var aggregateData = { data:{}, 
                            operating_systems:{ id:{}, order:[] } };

      for(var i=0; i<data.length; i++){
         //format unix timestamp
         var dt = new Date(data[i].date_run*1000);
         data[i]['readable_date'] = this.formatTimestamp(dt);

         /*********
          * Aggregate datastructure looks like this:
          *
          * ['data'][ product_id ][ test_id ][ operating_system_id ] =
          *   { average:[],
          *     min:[],
          *     max:[],
          *     standard_deviation:[],
          *     variance:[],
          *     revision:[],
          *     date_run:[],
          *     readable_date:[] }
          *
          *  Holds a list of unique operating system ids found 
          *  in the data, this is used to draw the vertical column 
          *  labels in the visualization
          *
          *  ['operating_systems'] = {os_id}
          *
          * *********/

         if( aggregateData['data'][ data[i].product_id ] === undefined ){
            aggregateData['data'][ data[i].product_id ] = {};
         }
         if( aggregateData['data'][ data[i].product_id ][ data[i].test_id ] === undefined ){
            aggregateData['data'][ data[i].product_id ][ data[i].test_id ] = {};
         }
         if( aggregateData['data'][ data[i].product_id ][ data[i].test_id ][ data[i].operating_system_id ] === undefined ){

            var values = { average:[],
                           min:[],
                           max:[],
                           standard_deviation:[],
                           variance:[],
                           revision:[],
                           date_run:[],
                           readable_date:[] };

            aggregateData['data'][ data[i].product_id ][ data[i].test_id ][ data[i].operating_system_id ] = values;
         }

         for(var j=0; j<this.adaptedDataFields.length; j++){
            aggregateData['data'][ data[i].product_id ][ data[i].test_id ][ data[i].operating_system_id ][ this.adaptedDataFields[j] ].push(data[i][ this.adaptedDataFields[j] ]);
         }

         //Build list of unique operating system ids
         if( !aggregateData['operating_systems']['id'][ data[i].operating_system_id ] ){
            aggregateData['operating_systems']['id'][ data[i].operating_system_id ] = 
               DV_PAGE.refData.operating_systems[ data[i].operating_system_id ].name + ' ' +
               DV_PAGE.refData.operating_systems[ data[i].operating_system_id ].version;

            aggregateData['operating_systems']['order'].push( data[i].operating_system_id );

         }
      }
      return aggregateData;
   },
   getVisData: function(){
      //Interface only function
      return [];
   },
   _configureGraphContainer: function(){

      //Hide the detail panels, they are not used by the visualization
      $(this.selectors.graph_detail).css('display', 'none');
      $(this.selectors.graph_detail_two).css('display', 'none');

      $(this.selectors.graph_container).removeClass('css-right');
      $(this.selectors.graph_container).addClass('css-left');
   },
   _drawTitleLabel: function(tile, productBranch, padding, width, height){

      var xAdjust = 0;
      if( productBranch[0] === undefined ){
         xAdjust = width - padding - 4*25;
      }else{
         xAdjust = width - padding - 4*productBranch[0].length;
      }

      for(var i=0; i<productBranch.length; i++){

         tile.append("svg:text")
             .data([productBranch[i].replace(/\n/, '')])
             .attr("x", function(d, i){ return xAdjust; })
             .attr("y", function(d){ return height - (5*padding) + (13*i); })
             .attr("text-anchor", "middle")
             .attr("font-size", 14)
             .attr("font-weight", "bold")
             .text(function(d, i){ return d; })
             .attr("fill", "black");
      } 
   },
   _drawLabel: function(label, padding, width, height){

      var svgTile = d3.select(this.selectors.graph_container)
                    .append("svg")
                      .attr("height", height)
                      .attr("width", width);

      var lineGroup = svgTile.append("svg:text")
                             .data([label.replace(/\n/, '')])
                             .attr("x", function(d, i){ return width - padding - 3*d.length; })
                             .attr("y", function(d){ return height - padding; })
                             .attr("text-anchor", "middle")
                             .attr("font-size", 12)
                             .text(function(d, i){ return d; })
                             .attr("fill", "black");

   },
   _drawEmptyTile: function(padding, width, height){
      var svgTile = d3.select(this.selectors.graph_container)
                    .append("svg")
                      .attr("height", height)
                      .attr("width", width);

      return svgTile;
   },
   _drawTile: function(data, padding, width, height){

      var max = d3.max(data.average);
      var min = d3.min(data.average);

      //REMOVE BEFORE RELEASE: Fake threshold for tile
      var threshold = d3.median(data.average);

      var x = d3.scale.linear().domain([1, data.average.length]).range([1, width]);
      x.clamp(true);
      var y = d3.scale.linear().domain([min, max+( (.5*height)+height)]).range([.3*height, height]);

      var productName = this.getProductName(data.product_id);
      var osName = this.getOsName(data.os_id);
      var testName = this.getTestName(data.test_id);

      this.signalData.label = productName + ', ' + testName + ', ' + osName;

      var signalData = "product_ids=" + data.product_id +
                       "&test_ids=" + data.test_id +
                       "&platform_ids=" + data.os_id;

      var dvData = JSON.stringify({ data:signalData,
                                    read_names:[ productName,
                                                 testName,
                                                 osName ], 
                                    padding:padding,
                                    width:width,
                                    height:height,
                                    //Cannot figure out how to maintain 
                                    //context with the "this" object in d3.
                                    //D3 automatically sets this to the DOM
                                    //element selected, wich in this case will
                                    //be the svg:g element for click events. To
                                    //compensate, I'm storing the data required to
                                    //send a signal as a "dv_data" attribute.
                                    signal_data:{ 'data':this.signalData,
                                                  'event':this.signalEvent,
                                                  'container':this.allViewsContainerSel } });

      var svgTile = d3.select(this.selectors.graph_container)
                    .append("svg")
                      .attr("height", height)
                      .attr("width", width)
                      .attr("dv_data", dvData);

      var lineGroup = svgTile.append("svg:g")
                             .attr("transform", "translate(" + padding + "," + height + ")")
                             .attr("opacity", 0.85)
                             .on('click', this._tileOnClick);

      var xLineFn = function(d, i){ return x(i); };
      var yLineFn = function(d) { return -1*y(d); };

      /*****
      var thresholdLine = d3.svg.line()
                            .x( xLineFn )
                            .y(function(d) { return -1*y(threshold); });
      ****/

      var baseLine = d3.svg.line()
                       .x( xLineFn )
                       .y(function(d) { return 0; });

      var area = d3.svg.area()
                   .x( xLineFn )
                   .y0(function(d) { return 0; })
                   .y1( yLineFn );

      //Mean area 
      lineGroup.append("svg:path")
               .attr("d", area(data.average) )
               .attr("fill", "steelblue")
               .attr("stroke-width", "2");

      // threshold line 
      /*******
      lineGroup.append("svg:path")
               .attr("d", thresholdLine(data.average) )
               .attr("stroke", "orange")
               .attr("stroke-width", "1.5");
      *********/

      // baseline
      lineGroup.append("svg:path")
               .attr("d", baseLine(data.average) )
               .attr("stroke", "black")
               .attr("stroke-width", "2");

      var stdData = data.standard_deviation;

      //standard deviation line
      var stdMax = d3.max(stdData);
      var stdMin = d3.min(stdData);
      var stdY = d3.scale.linear().domain([stdMin, stdMax+(.5*height)+height]).range([0, height]);

      var stdLine = d3.svg.line()
                      .x( xLineFn )
                      .y(function(d) { return -1*stdY(d + padding); });

      lineGroup.append("svg:path")
               .attr("d", stdLine(stdData) )
               .attr("stroke", "darkblue")
               .attr("fill", "none")
               .attr("opacity", 0.8)
               .attr("stroke-width", "1.5");
   },
   _tileOnClick: function(d, i){
                 
      var dvData = JSON.parse( $(this).parent().attr("dv_data") );

      var signalData = dvData.signal_data.data;

      signalData.data = dvData.data;
      signalData.read_names = dvData.read_names;
      signalData.signal = 'test_run_data';

      $(dvData.signal_data.container).trigger(dvData.signal_data.event, signalData); 


      if(DV_PAGE.selectionRect){
         DV_PAGE.selectionRect.remove();
      }
      DV_PAGE.selectionRect = d3.select(this)
                              .append("svg:rect")
                                 .attr("x", (.5*dvData.padding))
                                 .attr("y", -(dvData.height-(.5*dvData.padding)))
                                 .attr("width", dvData.width)
                                 .attr("height", dvData.height-dvData.padding)
                                 .attr("fill", "blue")
                                 .attr("opacity", 0.2)
                                 .attr("stroke", "darkblue")
                                 .attr("stroke-width", "5");
   }

});

var ScatterPlot = new Class({

   Extends:Visualization,

   jQuery:'DataViewAdapter',

   initialize: function(options){

      this.setOptions(options);
      this.parent(options);

      this.width = 700;
      this.height = 400;

      this.datasets = {}; 
      this.data = [];

      this.firstClick = true;
      this.firstUpdate = true;

      this.colorIndex = 0;
      this.colorScale = d3.scale.category10();
      this.selectedColors = {};

      this.mouseOverMessage = "Mouse over a data point to see the details";
      this.clickMessage = "Click on a data point to keep track of it here";

      //The data point indexes, set when a user
      //mouses over datapoint legends
      this.seriesIndexes = [];
      this.dataIndex = 0;

      this.keys = ['revision', 'mean', 'std', 'min', 'max', 'date_run'];

      this.datasetLegendSel = '#dv_legend';
      this.datasetTitleName = 'dv_dataset_title';
      this.datasetCbContainerName = 'dv_dataset_cb';
      this.datasetCloseName = 'dv_dataset_close';
      this.flotLabelClassSel = '.tickLabels';
      this.dataLegendClassSel = '.dv-vis-detail-panel';
      this.iconDisabledStateClass = 'ui-state-disabled';
      this.legendIdPrefix = 'dv_detail_';

      this.yAxisLabel = 'Run Time (milliseconds)';

      this.plotOptions = { legend:{ container:$(this.selectors.graph_detail),
                                    show: true },

                           yaxis: { autoscaleMargin:0.1 },

                           //xaxis:{ mode:'time'},

                           line:{ show:true, fill:true }, 

                           grid:{ clickable:true, 
                                  labelMargin:25,
                                  borderWidth:1,
                                  hoverable:true }};

   },
   display: function(data, menuToggle){

      this._configureGraphContainer();

      if(menuToggle){ 

         this._updatePlot();

      }else{

         //Load data into this.datasets
         this.adaptData(data);

         for(var key in this.datasets){
            if(this.datasets.hasOwnProperty(key)){
               this._displayDataset( key );
            }
         }
      }
   },
   adaptData: function(data){

      //Use datasetDetector to detect datasets already loaded
      var datasetDetector = this._cleanDatasets();

      for(var i=0; i<data.length; i++){

         var productId = data[i].product_id;
         var testId = data[i].test_id;
         var operatingSystemId = data[i].operating_system_id;

         var key = this._getDatasetKey([productId, testId, operatingSystemId]);

         if( this.datasets[key] === undefined ){


            var label = this._getLabel(productId, testId, operatingSystemId);

            this.datasets[ key ] = { data:this._getAdaptedDataStruct(),
                                     label:label, 
                                     xvalue:0,

/*
                                     cb_values:{ mean:{ value:true, index:[0] },
                                                 std:{ value:true, index:[1,2] },
                                                 minmax:{ value:false, index:[3,4] } },
 */

                                     key_data:{ product_id:productId,
                                                test_id:testId,
                                                operating_system_id:operatingSystemId },

                                     label_displayed:false,
                                     tick_times:{} };

         } else if( datasetDetector[key] === true ){
            //Dataset is already loaded, first time
            //encountering it in the database data, 
            //reset the adapted datastruct
            this.datasets[key]['xvalue'] = 0;
            this.datasets[key]['data'] = this._getAdaptedDataStruct();
            datasetDetector[key] = false;
         }

         //Used to display the mouseover data
         var displayObj = { test_run_id:data[i].test_run_id,
                            revision:data[i].revision, 
                            date_run:this.formatTimestamp(  new Date(data[i].date_run*1000) ),
                            mean:data[i].average,
                            max:data[i].max,
                            min:data[i].min,
                            std:data[i].standard_deviation };

         this.datasets[key].xvalue++;
         var xvalue = this.datasets[key].xvalue;
         //var xvalue = parseInt(data[i].date_run)*1000;

         //data structure used by flot to render the graph
         this.datasets[key].data.average.
                  push([xvalue, data[i].average, displayObj]); 
         this.datasets[key].data.std.
                  push([xvalue, data[i].standard_deviation, displayObj]); 
         this.datasets[key].data.std_min.
                  push([xvalue, data[i].average - data[i].standard_deviation, displayObj]); 
         this.datasets[key].data.std_max.
                  push([xvalue, data[i].average + data[i].standard_deviation, displayObj]); 
         this.datasets[key].data.min.
                  push([xvalue, data[i].min, displayObj]); 
         this.datasets[key].data.max.
                  push([xvalue, data[i].max, displayObj]); 

      }

   },
   getVisData: function(){
      var data = [];
      for( var id in this.datasets ){
         if(this.datasets.hasOwnProperty(id)){
            data.push( this.datasets[id]['key_data'] );
         }
      }
      return data;
   },
   _getAdaptedDataStruct: function(){
      return { average:[],
               std:[],
               std_min:[],
               std_max:[],
               min:[],
               max:[] };

   },
   _cleanDatasets: function(){

      //Use datasetDetector to detect datasets already loaded
      var datasetDetector = {};
      //reset xvalues for existing datasets
      for(var key in this.datasets){
         if(this.datasets.hasOwnProperty(key)){
            datasetDetector[key] = true;
         }
      }

      return datasetDetector;
   },
   _loadDataset: function(key){

      var color = "";
      if( this.datasets[key].color === undefined){
         //Get a new color
         color = this._getColor(key);
         this.datasets[key]['color'] = color;
      }else{
         //Reuse the existing color
         color = this.datasets[key]['color'];
      }

      //maps datasets to flot series ids
      this.datasets[key]['series_ids'] = { };
      //color associated with all of the dataset components
      this.datasets[key]['vis_data'] = { data:this.incomingSignalData.data, color:color };

      //This datastructure is for the flot option API
      this.datasets[key]['dataset'] = [ 
               { data: this.datasets[key].data.average,
                 color:color,
                 points:{show:true},
                 grid:{ show:true, clickable:true, hoverable:true },
                 id:'mean_' + key },

               { data: this.datasets[key].data.std_min,
                 color:color,
                 lines:{show:true, lineWidth:1, fill:false},
                 grid:{ clickable:true, hoverable:true },
                 id:'std_low_' + key },

               { data: this.datasets[key].data.std_max,
                 color:color,
                 grid:{ clickable:true, hoverable:true },
                 lines: { show:true, lineWidth:1, fill:false },
                 id:'std_high_' + key },

               { data: this.datasets[key].data.min,
                 color:color,
                 lines:{ show:true, lineWidth:0, fill:0.1 },
                 grid:{ clickable:true, hoverable:true },
                 id:'min_' + key },

               { data: this.datasets[key].data.max,
                 color:color,
                 lines: { show:true, lineWidth:0, fill:0.1 },
                 fillBetween:'min_' + key,
                 grid:{ clickable:true, hoverable:true },
                 id:'max_' + key } ];

      //Maps the checkbox values to their dataset positions in the 
      //this.datasets[key]['dataset']
      
      //Save the state of pre-existing graphs, only set the cb_values
      //if they have not been defined yet
      if( this.datasets[key]['cb_values'] === undefined ){

         this.datasets[key]['cb_values'] = { mean:{ value:true, index:[0] },
                                             std:{ value:true, index:[1,2] },
                                             minmax:{ value:false, index:[3,4] } };
      }
   },
   _getDatasetKey: function(data){

      var key = "";
      for(var j=0; j<data.length; j++){
         if(j === data.length-1){
            key += data[j];
         }else{
            key += data[j] + '-';
         }
      }

      return key;
   },
   _getLabel: function(productId, testId, operatingSystemId){

      var label = "";
      var productName = this.getProductAndBranch(productId);
      var testName = this.getTestName(testId);
      var platformName = this.getOsName(operatingSystemId);

      if(productName){
         label += productName;
      }
      if(testName){
         label += ', ' + testName;
      }
      if(platformName){
         label += ', ' + platformName;
      }

      return label;
   },
   _displayDataset: function(key){

      this._loadDataset(key);

      if(this.datasets[key].label_displayed === false){
         this._getLabelContainer(key);
         this.datasets[key].label_displayed = true;
      }

      this._updatePlot();

      if(this.firstUpdate === true){ 

         var detailCardEl = this._getDetailCard(this.colorScale(0));
         $(detailCardEl).text( this.mouseOverMessage );
         $(this.selectors.hover_detail).empty();
         $(this.selectors.hover_detail).append(detailCardEl);

         var detailCardTwoEl = this._getDetailCard(this.colorScale(0));
         $(detailCardTwoEl).text( this.clickMessage );
         $(this.selectors.click_detail).append(detailCardTwoEl);

         this.firstUpdate = false;
      }

   },
   _formatXaxisTick: function(val, axis){
      //Remove time stamp
      //var formattedTime = this.tickTimes[val];
      //if(this.tickTimes[val] != undefined){
      //   formattedTime = this.tickTimes[val].replace(/\s\S+$/, '');
      //}
      //return formattedTime;
      return "";
   },
   _updatePlot: function(){

      this._loadData();

      if(this.plot){
         this.plot.shutdown();
         $(this.selectors.graph_container).unbind('plotclick');
         $(this.selectors.graph_container).unbind('plothover');
      }

      this.plot = $.plot( $(this.selectors.graph_container), this.data, this.plotOptions);

      this._setYaxisLabel(this.yAxisLabel);

      $(this.selectors.graph_container).bind('plotclick', _.bind(this._clickPlot, this));
      $(this.selectors.graph_container).bind('plothover', _.bind(this._hoverPlot, this));
   },
   _loadData: function(){

      this.data = [];

      for(var key in this.datasets){

         if(this.datasets.hasOwnProperty(key)){

            //Clean out the existing series ids
            this.datasets[key]['series_ids'] = {};

            for(var cbType in this.datasets[key]['cb_values']){
               if( this.datasets[key]['cb_values'].hasOwnProperty(cbType) ){
                  //Make sure cb is toggled on
                  if( this.datasets[key]['cb_values'][cbType].value ){
                     for(var i=0; i<this.datasets[key]['cb_values'][cbType].index.length; i++){

                        var index = this.datasets[key]['cb_values'][cbType].index[i];

                        var dataLength = 0;
                        if( this.datasets[key].dataset[index] != undefined ){
                           dataLength =  this.data.push( this.datasets[key].dataset[index] );
                        }

                        if( !this.datasets[key]['series_ids'][cbType] ){
                           this.datasets[key]['series_ids'][cbType] = [];
                        }
                        this.datasets[key]['series_ids'][cbType].push(dataLength - 1);
                     }
                  }
               }
            }
         }
      }
   },
   _getLabelContainer: function(key){

      //Add alpha channel to lighten the color
      var rgbAlpha = this._getAlphaChannelColor( this.datasets[key].color);

      var legendClone = $(this.datasetLegendSel).clone();

      $(legendClone).attr('id', this.legendIdPrefix + key);

      var titleDiv = $(legendClone).find('[name="' + this.datasetTitleName + '"]');

      $(titleDiv).text( this.datasets[key].label );

      var cbContainer = $(legendClone).find('[name="' + this.datasetCbContainerName + '"]');

      var dataTypes = [{name:'mean', 
                        display:'mean', 
                        title:'Average runtime', 
                        checked:true,
                        margin:'margin-top:5px;'}, 

                       {name:'std', 
                        display:'std', 
                        checked:true,
                        title:'Standard deviation', 
                        margin:'margin-top:5px;'},

                       {name:'minmax', 
                        display:'min & max', 
                        checked:false,
                        title:'The minimum and maximum value plotted as an area', 
                        margin:'margin-top:4px;'}];

      for(var i=0; i<dataTypes.length; i++){

         var cb = "";
         var cbName = this._getCbName(dataTypes[i].name, key);

         if( dataTypes[i].checked === true ){
            cb = $('<input class="css-left" type="checkbox" name="' + 
                    cbName + '" checked />' +
                    '<div class="css-left" style="' + dataTypes[i].margin + '" title="' + 
                    dataTypes[i].title + '">' + dataTypes[i].display + '</div>');
         }else{
            cb = $('<input class="css-left" type="checkbox" name="' + 
                    cbName + '" />' +
                    '<div class="css-left" style="' + dataTypes[i].margin + '" title="' + 
                    dataTypes[i].title + '">' + dataTypes[i].display + '</div>');
         }

         //Assign checkbox click event
         $(cb).bind('click', _.bind( this._clickCb, this ));

         $(cbContainer).append(cb);
      }

      $(legendClone).css('background-color', rgbAlpha);
      $(legendClone).css('border-color', this.datasets[key].color);
      $(legendClone).css('border-width', 2);
      $(legendClone).css('display', 'block');

      $(this.selectors.graph_detail).append(legendClone);

      //Assign close events
      var closeEl = $(legendClone).find('[name="' + this.datasetCloseName + '"]');
      $(closeEl).bind('click', _.bind( this._closeDataset, this ));

   },
   _getCbName: function(name, key){
      //Use the parent_dview_index to insure we have a unique name
      return this.signalData.parent_dview_index + '_' + name + '_' + key;
   },
   _getColor: function(){

      /*************
       * For most use cases 10 colors is plenty, by using the
       * d3 scale we are assured that the first 10 colors are visually
       * distinct and won't burn holes in the user's eyes.  Once we
       * exceed 10, use a random color generator and make sure we don't
       * re-use a color in use.  The random colors might not be as 
       * visually distinct.
       * ************/
      var color = "";

      if( (this.incomingSignalData.color != undefined) &&
          (this.incomingSignalData.color != "") ){
         color = this.incomingSignalData.color;
      }else{

         if(this.colorIndex > 10){
            var uniqueColor = false;
            while (!uniqueColor) {
               //Generate a random hex color value
               color = '#'+((1<<24)*(Math.random()+1)|0).toString(16).substr(1);
               if(!this.selectedColors[color]){
                  //This color has not been used before
                  uniqueColor = true;   
               }
            }

         }else{
            //Use the d3 color scale
            color = this.colorScale(this.colorIndex); 
         }

         this.colorIndex++;

         this.selectedColors[color] = true;
      }

      return color;
   },
   _closeDataset: function(e){

      var container = $(e.target).closest('div[id*="' + this.legendIdPrefix + '"]');
      var id = $(container).attr('id');

      var idObj = this._getIndexFromId(id);

      this._deleteDataset(idObj.index);
      this._updatePlot();

      $(container).remove();

   },
   _clickCb: function(e){

      var name = $(e.target).attr('name');

      if(name){
         var nameFields = name.split('_');
         var checked = $(e.target).attr('value');
         var cbType = nameFields[1];
         var key = nameFields[2];

         if(this.datasets[key]['cb_values'][cbType].value === true){
            this.datasets[key]['cb_values'][cbType].value = false;
         }else{
            this.datasets[key]['cb_values'][cbType].value = true;
         }

         //reset current hover selections
         this.seriesIndexes = [];
         this.dataIndex = 0;

         this._updatePlot();
      }

   },
   _deleteDataset: function(index){

      //reset current hover selections
      this.seriesIndexes = [];
      this.dataIndex = 0;

      this.datasets[index].dataset = [];

      delete( this.datasets[index] );

   },
   _clickPlot: function(e, pos, item){

      if(item){

         var color = item.series.color;
         var detailCardEl = this._getDetailCard(color, item);
         this._setDisplayDivData(item, detailCardEl, item.series.id, color);

         if(this.firstClick === true){ 
            $(this.selectors.click_detail).empty();
            this.firstClick = false;
         }

         $(this.selectors.click_detail).prepend(detailCardEl);

         this.signalData.signal = 'test_run_id';

         var displayObj = this._getDisplayObj(item);
         var revision = this.getRevision(displayObj.revision);

         var a = $(displayObj.test_run_id).find('a');
         this.signalData.data = 'test_run_id=' + $(a).text();
         this.signalData.color = color;

         this.signalData.read_names = [ revision, this.incomingSignalData.read_names ];

         var idObj = this._getIndexFromId(item.series.id);
         this.signalData.label = revision + ', ' + this.datasets[idObj.index].label;

         $(this.allViewsContainerSel).trigger(this.signalEvent, this.signalData); 

      }

   },
   _hoverPlot: function(e, pos, item){

      if(item){

         var color = item.series.color;

         var detailCardEl = this._getDetailCard(color, item);

         //Disable the close icon
         var closeAnchor = $(detailCardEl).find('a');
         $(closeAnchor).addClass(this.iconDisabledStateClass);
         $(closeAnchor).unbind();

         this._setDisplayDivData(item, detailCardEl, item.series.id, color);

         $(this.selectors.hover_detail).empty();
         $(this.selectors.hover_detail).append(detailCardEl);
      }
   },
   _getDetailCard: function(color, item){

      var legendClone = $(this.datasetLegendSel).clone();

      $(legendClone).attr('id', '');

      //Add alpha channel to lighten the background color
      var rgbAlpha = this._getAlphaChannelColor(color);
      $(legendClone).css('background-color', rgbAlpha);

      //Add full color to border
      $(legendClone).css('border-color', color);
      $(legendClone).css('border-width', 2);
      $(legendClone).css('display', 'block');

      $(legendClone).bind('mouseover', _.bind(this._mouseOverDatapointLegend, this, item, legendClone, color ));
      $(legendClone).bind('mouseout', _.bind(this._mouseOutDatapointLegend, this, item, legendClone, color ));

      var dataLegendClassSel = this.dataLegendClassSel;
      var closeEl = $(legendClone).find('[name="' + this.datasetCloseName + '"]');
      $(closeEl).bind('click', function(e){
         var legend = $(e.target).closest(dataLegendClassSel);
         legend.remove();
      });

      return legendClone;
   },
   _getDisplayDiv: function(key, data, underline){
      var el = "";
      if(underline){
         el = $('<div class="css-left" style="margin-left:10px; text-decoration:underline;"><strong>' + key + ':' + data + '</strong></div>');
      }else{
         el = $('<div class="css-left" style="margin-left:10px;"><strong>' + key + ':</strong>' + data + '</div>');
      }

      return el;
   },
   _getDisplayObj: function(item){
      return item.series.data[ item.dataIndex ][2];
   },
   _setDisplayDivData: function(item, detailCardEl, seriesId, color){

      var displayObj = this._getDisplayObj(item);

      for(var i=0; i<this.keys.length; i++){
         var underline = false;
         if(seriesId.match(this.keys[i])){
            underline = true;
         }
         var el = this._getDisplayDiv(this.keys[i], displayObj[ this.keys[i] ], underline);
         if(this.keys[i] === 'revision'){
            var a = $(el).find('a');
            a.css('color', color);
            a.css('font-weight', 'bold');
         }
         $(detailCardEl).append(el);
      }

   },
   _mouseOutDatapointLegend: function(item, legendClone, color){
      var alphaColor = this._getAlphaChannelColor(color);
      $(legendClone).css('background-color', alphaColor);
      this._unhighlightDatapoints(this.seriesIndexes, this.dataIndex);
   },
   _mouseOverDatapointLegend: function(item, legendClone, color){

      if(item){

         var idObj = this._getIndexFromId(item.series.id);

         if(this.datasets[idObj.index] === undefined){
            //dataset has been deleted don't try to highlight
            return;
         }

         var dataIndex = item.dataIndex;
         var seriesIndexes = this._getSeriesIndexesFromFlotId(idObj.index, item.series.id);

         this._unhighlightDatapoints(this.seriesIndexes, this.dataIndex);
         this._highlightDatapoints(seriesIndexes, dataIndex);

         this.seriesIndexes = seriesIndexes;
         this.dataIndex = dataIndex;

         $(legendClone).css('background-color', '#FFFFFF');
      }
   },
   _getIndexFromId: function(id){
      var idObj = { field_one:"", index:0 };
      if(id != undefined){
         var idFields = id.split('_');
         idObj.field_one = idFields[ 0 ];
         idObj.index = index = idFields[ idFields.length - 1 ];
      }
      return idObj;
   },
   _getSeriesIndexesFromFlotId: function(index, flotId){
      var idObj = this._getIndexFromId( flotId );
      var seriesIndexes = [];
      for(var cb in this.datasets[index]['series_ids']){
         if(this.datasets[index]['series_ids'].hasOwnProperty(cb)){
            for(var j=0; j<this.datasets[index]['series_ids'][cb].length; j++){
               seriesIndexes.push( this.datasets[index]['series_ids'][cb][j] );
            }
         }
      }
      return seriesIndexes;
   },
   _highlightDatapoints: function(seriesIndexes, datapoint){
      for(var i=0; i<seriesIndexes.length; i++){
         this.plot.highlight(seriesIndexes[i], datapoint);
      }
   },
   _unhighlightDatapoints: function(seriesIndexes, datapoint){
      for(var i=0; i<seriesIndexes.length; i++){
         this.plot.unhighlight(seriesIndexes[i], datapoint);
      }
   },
   _getAlphaChannelColor: function(color){
      var rc = d3.rgb(color);
      var rgbAlpha = 'rgba(' + rc['r'] + ',' + rc['g'] + ',' + rc['b'] + ',0.1)';
      return rgbAlpha;
   },
   _setYaxisLabel: function(label){
      var labelEl = $('<div class="css-left dv-verticaltext" style="position:absolute;' + 
                      ' top:235px; right:' + this.width + 'px;">' + label + '</div>');
      var yaxisLabelContainer = $(this.selectors.graph_container).find(this.flotLabelClassSel);

      $(yaxisLabelContainer).append(labelEl);
   },
   _configureGraphContainer: function(){

      this.setGraphContainerSize(this.width, this.height);

      $(this.selectors.graph_detail).css('display', 'block');
      $(this.selectors.graph_detail_two).css('display', 'block');

      $(this.selectors.graph_container).removeClass('css-left');
      $(this.selectors.graph_container).addClass('css-right');

      var w1 = parseInt( $(this.selectors.graph_detail).css('width') );
      var w2 = this.width;
      var w3 = parseInt( $(this.selectors.graph_container).css('margin-left') );
      $(this.selectors.graph_detail_container).css('width', w1 + w2 + w3);

   }
});
var BoxPlot = new Class({

   Extends:Visualization,

   jQuery:'DataViewAdapter',

   initialize: function(options){

      this.setOptions(options);
      this.parent(options);
     
      this.urls = {};

   },
   display: function(data, menuToggle){

      this.clearContainers(this.selectors);

      this._configureGraphContainer();
      
      this.adaptData(data);

      var widthMultiplier = parseInt( _.size(this.urls) );

      drawBoxPlot(data, this.selectors.graph_container, widthMultiplier); 
      
   },
   adaptData: function(data){

      for(var i=0; i<data.length; i++){
         this.urls[data[i].url] = true;
      }

   },
   getVisData: function(){
      //Interface only function
      return [];
   },
   _configureGraphContainer: function(){
      //Hide the detail panels, they are not used by the visualization
      $(this.selectors.graph_detail).css('display', 'none');
      $(this.selectors.graph_detail_two).empty('display', 'none');

      $(this.selectors.graph_container).removeClass('css-right');
      $(this.selectors.graph_container).addClass('css-left');
   }
});

var ScatterLabelPlot = new Class({

   Extends:ScatterPlot,

   jQuery:'DataViewAdapter',

   initialize: function(options){

      this.setOptions(options);
      this.parent(options);

      this.keys.push('url');

      this.plotOptions['xaxis'] = { show:false };

      this.xlabelClass = 'dv-horizontaltext';
      this.xlabel = 'URL in Test Pageset';

   },
   adaptData: function(data){

      var datasetDetector = this._cleanDatasets();
      for(var i=0; i<data.length; i++){

         var productId = data[i].product_id;
         var testId = data[i].test_id;
         var operatingSystemId = data[i].operating_system_id;
         var revision = this.getRevision( data[i].revision );

         var key = revision + '-' + this._getDatasetKey([productId, testId, operatingSystemId]);

         if( this.datasets[key] === undefined ){

            var label = revision + ' ' + this._getLabel(productId, testId, operatingSystemId);

            var a = $(data[i].test_run_id).find('a');
            var testRunId = parseInt( a.text() );

            this.datasets[ key ] = { data:this._getAdaptedDataStruct(),
                                     label:label, 
                                     key_data:{ revision: revision,
                                                product_id:productId,
                                                test_id:testId,
                                                test_run_id:testRunId,
                                                operating_system_id:operatingSystemId },
                                     label_displayed:false,
                                     xvalue:0,
                                     tick_times:{} };
         }else if( datasetDetector[key] === true ){
            //Dataset is already loaded, first time
            //encountering it in the database data, 
            //reset the adapted datastruct
            this.datasets[key]['xvalue'] = 0;
            this.datasets[key]['data'] = this._getAdaptedDataStruct();
            datasetDetector[key] = false;
         }

         this.datasets[ key ].xvalue++;
         var xvalue = this.datasets[ key ].xvalue++;

         var displayObj = { test_run_id:data[i].test_run_id,
                            page_id:data[i].page_id, 
                            revision:revision, 
                            date_run:this.formatTimestamp(  new Date(data[i].date_run*1000) ),
                            mean:data[i].average,
                            max:data[i].max,
                            min:data[i].min,
                            std:data[i].standard_deviation,
                            url:data[i].url };

         //data structure used by flot to render the graph
         this.datasets[key].data.average.
                  push([xvalue, data[i].average, displayObj]); 
         this.datasets[key].data.std.
                  push([xvalue, data[i].standard_deviation, displayObj]); 
         this.datasets[key].data.std_min.
                  push([xvalue, data[i].average - data[i].standard_deviation, displayObj]); 
         this.datasets[key].data.std_max.
                  push([xvalue, data[i].average + data[i].standard_deviation, displayObj]); 
         this.datasets[key].data.min.
                  push([xvalue, data[i].min, displayObj]); 
         this.datasets[key].data.max.
                  push([xvalue, data[i].max, displayObj]); 

      }
   },
   _setXaxisLabel: function(label){
      var xlabelContainer = $(this.selectors.graph_detail_two).find('.' + this.xlabelClass);
      $(xlabelContainer).empty();
      var labelEl = $('<div class="' + this.xlabelClass + '">' + this.xlabel + '</div>');
      $(this.selectors.graph_detail_two).prepend(labelEl);
   },
   _updatePlot: function(){

      this._loadData();

      if(this.plot){
         this.plot.shutdown();
         $(this.selectors.graph_container).unbind('plotclick');
         $(this.selectors.graph_container).unbind('plothover');
      }
      this.plot = $.plot( $(this.selectors.graph_container), this.data, this.plotOptions);

      this._setXaxisLabel(this.yAxisLabel);
      this._setYaxisLabel(this.yAxisLabel);

      $(this.selectors.graph_container).bind('plotclick', _.bind(this._clickPlot, this));
      $(this.selectors.graph_container).bind('plothover', _.bind(this._hoverPlot, this));
   },
   _clickPlot: function(e, pos, item){

      if(item){

         var color = item.series.color;
         var detailCardEl = this._getDetailCard(color, item);
         this._setDisplayDivData(item, detailCardEl, item.series.id, color);

         if(this.firstClick){ 
            $(this.selectors.click_detail).empty();
            this.firstClick = false;
         }

         $(this.selectors.click_detail).prepend(detailCardEl);

         this.signalData.signal = 'test_run_id';

         var displayObj = this._getDisplayObj(item);

         var a = $(displayObj.test_run_id).find('a');
         this.signalData.data = 'test_run_id=' + $(a).text() + '&page_id=' + displayObj.page_id;

         this.signalData.read_names = [ displayObj.revision, displayObj.url, this.incomingSignalData.read_names ];
         this.signalData.color = color;

         //Set the label for signal display in the dataview
         var idObj = this._getIndexFromId(item.series.id);
         this.signalData.label = this.datasets[idObj.index].label;

         var idObj = this._getIndexFromId(item.series.id);
         this.signalData.label = displayObj.url + ', ' + this.datasets[idObj.index].label;

         $(this.allViewsContainerSel).trigger(this.signalEvent, this.signalData); 

      }
   }
});


var SideBarPlot = new Class({

   Extends:ScatterPlot,

   jQuery:'DataViewAdapter',

   initialize: function(options){

      this.setOptions(options);
      this.parent(options);

      this.plotOptions['bars'] = { show:true, fill:true };
      this.plotOptions['xaxis'] = { tickFormatter: _.bind(this._formatXTick, this) };
      this.plotOptions['tickSize'] = 1;
      this.keys = ['revision', 'run_id', 'value', 'date_run', 'url'];

      this.barWidth = 0.9;

      this.barWidths = [ 0.9, 0.3, 0.2, 0.15, 0.125,
                         0.100, 0.074, 0.0725, 0.0600,
                         0.0450, 0.0350, 0.0250, 0.0150 ];

      this.barMinWidth = 0.010;

      this.xLabelTextTag = "Run ";
   },
   adaptData: function(data){

      var datasetDetector = this._cleanDatasets();

      for(var i=0; i<data.length; i++){

         var productId = data[i].product_id;
         var testId = data[i].test_id;
         var operatingSystemId = data[i].operating_system_id;
         var revision = this.getRevision( data[i].revision );
         var url = data[i].url;

         var pa = $(data[i].page_id).find('a');
         var pageId = parseInt( pa.text() );

         var key = revision + '-' + pageId + '-';
         key += this._getDatasetKey([productId, testId, operatingSystemId]);

         var displayObj = this._getAdaptedDataStruct(data[i]);

         if( this.datasets[key] === undefined ){

            var label = revision + ' ' + url;
            label += ' ' + this._getLabel(productId, testId, operatingSystemId);

            var a = $(data[i].test_run_id).find('a');
            var testRunId = parseInt( a.text() );

            this.datasets[ key ] = { label:label, 
                                     data:[],
                                     key_data:{ revision:revision,
                                                product_id:productId,
                                                test_id:testId,
                                                test_run_id:testRunId,
                                                page_id:pageId,
                                                operating_system_id:operatingSystemId },
                                     label_displayed:false };

         } else if( datasetDetector[key] === true ){
            //Dataset is already loaded, first time
            //encountering it in the database data, 
            //reset the adapted datastruct
            //this.datasets[key]['data'] = [];
            datasetDetector[key] = false;
         }

         this.datasets[key]['data'].push( [data[i].run_id, 
                                           data[i].value, 
                                           displayObj] );
      }

   },
   _getAdaptedDataStruct: function(data){

      var displayObj = { test_run_id:data.test_run_id,
                         revision:this.getRevision(data.revision), 
                         value:data.value, 
                         run_id:data.run_id, 
                         date_run:this.formatTimestamp(  new Date(data.date_run*1000) ),
                         url:data.url };

      return displayObj;

   },
   _loadDataset: function(key){
      var color = "";
      if( this.datasets[key].color === undefined){
         //Get a new color
         color = this._getColor(key);
         this.datasets[key]['color'] = color;
      }else{
         //Reuse the existing color
         color = this.datasets[key]['color'];
      }

      this.datasets[key]['dataset'] = [ 
               { data:this.datasets[key]['data'],
                 color:color,
                 bars:{ show:true, order:1 },
                 grid:{ show:true, clickable:true, hoverable:true },
                 id:'box_' + key } ];
   },
   _loadData: function(){
      //Set the bar width according to how many datasets are on
      //the graph
      this._setBarWidth();

      this.data = [];
      for(var id in this.datasets){

         if(this.datasets[id]['dataset'] === undefined){
            continue;
         }
         if(this.datasets.hasOwnProperty(id)){

            this.datasets[id]['series_ids'] = 0;

            for( var i=0; i<this.datasets[id].dataset.length; i++ ){
               this.datasets[id].dataset[i].bars.barWidth = this.barWidth;
               var dataLength = this.data.push( this.datasets[id].dataset[i] );
               this.datasets[id]['series_ids'] = dataLength - 1;
            }
         }
      }
   },
   _updatePlot: function(){

      this._loadData();

      if(this.plot){
         this.plot.shutdown();
         $(this.selectors.graph_container).unbind('plotclick');
         $(this.selectors.graph_container).unbind('plothover');
      }
      this.plot = $.plot( $(this.selectors.graph_container), this.data, this.plotOptions);

      this._setYaxisLabel(this.yAxisLabel);

      $(this.selectors.graph_container).bind('plotclick', _.bind(this._clickPlot, this));
      $(this.selectors.graph_container).bind('plothover', _.bind(this._hoverPlot, this));
   },
   _setBarWidth: function(){
      var size = _.size(this.datasets);
      if( this.barWidths[ size-1 ] ){
         this.barWidth = this.barWidths[ size-1 ];
      }else{
         this.barWidth = this.barMinWidth;
      }
   },
   _setDisplayDivData: function(item, detailCardEl, seriesId, color){

      var displayObj = this._getDisplayObj(item);

      for(var i=0; i<this.keys.length; i++){
         var underline = false;
         var el = this._getDisplayDiv(this.keys[i], displayObj[ this.keys[i] ], underline);
         if(this.keys[i] === 'revision'){
            var a = $(el).find('a');
            a.css('color', color);
            a.css('font-weight', 'bold');
         }
         $(detailCardEl).append(el);
      }

   },
   _getLabelContainer: function(key){

      //Add alpha channel to lighten the color
      var rgbAlpha = this._getAlphaChannelColor( this.datasets[key].color );

      var legendClone = $(this.datasetLegendSel).clone();

      $(legendClone).attr('id', this.legendIdPrefix + key);

      var titleDiv = $(legendClone).find('[name="' + this.datasetTitleName + '"]');

      //Set the label on the legend element
      $(titleDiv).text( this.datasets[key].label );

      $(legendClone).css('background-color', rgbAlpha);
      $(legendClone).css('border-color', this.datasets[key].color);
      $(legendClone).css('border-width', 2);
      $(legendClone).css('display', 'block');

      $(this.selectors.graph_detail).append(legendClone);

      //Assign close events
      var closeEl = $(legendClone).find('[name="' + this.datasetCloseName + '"]');
      $(closeEl).bind('click', _.bind( this._closeDataset, this ));

   },
   _getSeriesIndexesFromFlotId: function(index, flotId){
      var idObj = this._getIndexFromId( flotId );
      var seriesIndexes = [];
      seriesIndexes.push( this.datasets[idObj.index]['series_ids'] );
      return seriesIndexes;
   },
   _unhighlightDatapoints: function(seriesIndexes, datapoint){
      /******
       * Not sure why the base class _unhighlightDatapoints does not work
       * for the bars.  The seriesIndexes/datapoint are correct, could be a 
       * bug in flot.  Calling unhighlight() with no arguments removes all
       * selections on the chart.
       * ****/
      this.plot.unhighlight();
   },
   _formatXTick: function(tickNumber, tickObject){
console.log( ['tickNumber', tickNumber] );
      return this.xLabelTextTag + parseInt( tickNumber );
   }

});
