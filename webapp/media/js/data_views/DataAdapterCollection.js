/******* 
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this file,
 * You can obtain one at http://mozilla.org/MPL/2.0/. 
 * *****/
var DataAdapterCollection = new Class({
   /****************************
    * DataAdapterCollection holds an associative array
    * of DataViewAdapter classes.  These adapter classes enable
    * individual dviews to deliver idiosyncratic behavior that
    * is unique to the data that they deliver.  Callers call
    * getAdapter('adapter_name') to retrieve a specific dview adapter.
    * **************************/

   Extends:Options,

   jQuery:'DataViewAdapterCollection',

   initialize: function(selector, options){

      this.setOptions(options);

      //Holds a list of adapters.  The key should be found in
      //views.json in the data_adapter attribute.
      this.adapters = { 'named_fields':new DataViewAdapter(),
                        'test_selector':new TestSelectorAdapter() };

   },

   getAdapter: function(adapter){

      if(this.adapters[adapter] === undefined){
         this.adapters['named_fields'].adapter = adapter;
         return this.adapters['named_fields'];
      }else{
         this.adapters[adapter].adapter = adapter;
         return this.adapters[adapter];
      }
   }
});
var DataViewAdapter = new Class({
   /**************************
    * The DataViewAdapter provides functionality for managing 
    * the generic dview.  The public interface includes all
    * dview functionality that might need to be specialized.
    * New types of dviews can inherit from DataViewAdapter and
    * override the public interface where necessary.
    *
    *     Public Interface
    *     ----------------
    *     setControlPanelFields()
    *     processControlPanel()
    *     clearPanel()
    *     getDefaultParams()
    *     processData()
    *     processPanelClick()
    *     setSelectionRange()
    *
    **************************/
   Extends:Options,

   jQuery:'DataViewAdapter',

   initialize: function(selector, options){

      this.setOptions(options);

      this.mercurialUrlBase = "http://hg.mozilla.org/BRANCH/rev/";

      //Name of the adapter, set by getAdapter()
      this.adapter = "";
      //Set's the default column to sort on
      this.sorting = { 'named_fields':[[0, 'desc']] };

      this.formatColumnMap = { revision:_.bind(this._externalLinkFormatter, this) };

      this.cpStartDateName = 'start_date';
      this.cpEndDateName = 'end_date';

      this.startDateSel = '#dv_start_date';
      this.endDateSel = '#dv_end_date';
      this.currentDateSel = '#dv_current_date';

      this.ignoreKeyCodes = { 37:1,    //left arrow
                              39:1 };  //right arrow

      //Use for determining clone id values
      this.view = new View();
   },
   setControlPanelFields: function(controlPanelDropdownEl, data, dhviewIndex){

      /*********************
       * Sets the values of the input fields in the control panel.  These 
       * fields may need to be pre-loaded with default values or the data 
       * from a particular signal.
       *
       * Parameters:
       *   
       *    controlPanelDropdownEl - The control panel DOM element
       *
       *    data - signal data object
       *             data.signal - name of signal
       *             data.data - signal data
       * *******************/
      if(!_.isEmpty(data)){

         var el = $(controlPanelDropdownEl).find('[name="' + data.signal + '"]');
         $(el).attr('value', DV_PAGE.unescapeForUrl(data.data));

         if(!_.isEmpty(data.date_range)){
            var startInput = $(controlPanelDropdownEl).find('[name="start_date"]');
            startInput.attr('value',  data.date_range.start_date );
            var endInput = $(controlPanelDropdownEl).find('[name="end_date"]');
            endInput.attr('value', data.date_range.end_date );
         }
      }else {

         var startInput = $(controlPanelDropdownEl).find('[name="start_date"]');
         var endInput = $(controlPanelDropdownEl).find('[name="end_date"]');

         //Only set the values to the default date range if both values
         //are undefined
         if( !startInput.val() && !endInput.val() ){ 
            startInput.attr('value',  $(this.startDateSel).val() );
            endInput.attr('value', $(this.endDateSel).val() );
         }
      }
   },
   processControlPanel: function(controlPanelSel, data, dviewIndex){
      /*************************
       * Translate the values of the control panel fields 
       * or signal data into a URL parameter string.
       *
       * Parameters:
       *    
       *    controlPanelSel - Control panel id selector
       *    data - signal data object
       *       data.signal - name of signal
       *       data.data - signal data
       **************************/
      var params = "";

      if(!_.isEmpty(data)){
         if(!_.isEmpty(data.date_range)){
            params = 'start_date=' + data.date_range.start_date + 
                     '&end_date=' + data.date_range.end_date + '&' + 
                     data.signal + '=' + data.data; 
         }else{
            params = data.signal + '=' + data.data; 
         }
      }else{

         var inputs = $(controlPanelSel).find('input');

         for(var i=0; i<inputs.length; i++){
            var type = $(inputs[i]).attr('type');
            if((type === 'text') || (type === 'checkbox') || (type === 'hidden')){
               var name = $(inputs[i]).attr('name');
               var v = $(inputs[i]).val();
               if(v != undefined){
                  v = v.replace(/\s+$/, '');
               }
               if(!(v === "")){
                  params += name + '=' + DV_PAGE.escapeForUrl(v) + '&';
               }
            }
         }
         var textareas = $(controlPanelSel).find('textarea');
         for(var i=0; i<textareas.length; i++){
            var name = $(textareas[i]).attr('name');
            var v = $(textareas[i]).val();
            if(!(v === "")){
               params += name + '=' + DV_PAGE.escapeForUrl(v) + '&';
            }
         }
         params = params.replace(/\&$/, '');

      }

      if(params === ""){
         //If params is still an empty string it's possible processControlPanel
         //was called before the control panel was created.  Get the date range
         var dateRange = this.getDateRangeParams(controlPanelSel, data);
         params = "start_date=" + dateRange.start_date + "&end_date=" + dateRange.end_date;
      }
      return params;
   },
   getDateRangeParams: function(controlPanelDropdownEl, signalData){

      var start = "";
      var end = "";

      if(($(controlPanelDropdownEl)[0] === undefined) && (signalData === undefined)){
         //Menu has not been created take date range out of page
         start = $(this.startDateSel).val();
         end = $(this.endDateSel).val();
      }else{
         //Menu has been created already
         var startInput = $(controlPanelDropdownEl).find('[name="start_date"]');
         start = startInput.val();
         if(start != undefined){
            start = start.replace(/\s+$/, '');
         }
         var endInput = $(controlPanelDropdownEl).find('[name="end_date"]');
         end = endInput.val();
         if(end != undefined){
            end = end.replace(/\s+$/, '');
         }

         //signal data exists but the menu has not been created, could occur on refresh
         //or navigating to another view
         if( ((start === undefined) && (end === undefined)) && (signalData['date_range'] != undefined)){
            return signalData['date_range'];
         }
      }

      return { start_date:start, end_date:end };
   },
   clearPanel: function(controlPanelSel){
      /*******************
       * Clear all of the input fields in the control panel.
       *
       * Parameters:
       *    controlPanelSel - Control panel id selector
       ********************/
      var inputs = $(controlPanelSel).find('input');
      var textareas = $(controlPanelSel).find('textarea');
      for(var i=0; i<inputs.length; i++){
         $(inputs[i]).attr('value', '');
      }
      for(var i=0; i<textareas.length; i++){
         $(textareas[i]).attr('value', '');
      }
   },
   getDefaultParams: function(){
      /******************
       * Build the default URL parameter string.  In this case
       * use the date range embedded in the page.
       * ****************/
      var params = 'start_date=' + $(this.startDateSel).val() +
                   '&end_date=' + $(this.endDateSel).val();
      return params;
   },
   resetDates: function(controlPanelDropdownEl){

      //Reset the start and end date to the values embedded
      //in the page.
      var startInput = $(controlPanelDropdownEl).find('[name="start_date"]');
      startInput.attr('value', $(this.startDateSel).val());

      var endInput = $(controlPanelDropdownEl).find('[name="end_date"]');
      endInput.attr('value', $(this.endDateSel).val());
   },
   checkDates: function(controlPanelDropdownEl, 
                        showMessage, 
                        serverStartDate, 
                        serverEndDate, 
                        serverResetSel,
                        badDateSel){

      this.serverResetSel = serverResetSel;
      this.badDateSel = badDateSel;

      var startInput = $(controlPanelDropdownEl).find('[name="start_date"]');
      var endInput = $(controlPanelDropdownEl).find('[name="end_date"]');

      //Check if the server reset the date range 
      if( showMessage ){
         //update panel values
         startInput.attr('value', serverStartDate);
         endInput.attr('value', serverEndDate);
         //display message
         $(this.serverResetSel).removeClass('hidden');
      }else{
         $(this.serverResetSel).addClass('hidden');
         $(this.badDateSel).addClass('hidden');
      }

      //Set up date format listeners
      startInput.keyup( _.bind(this.validateDate, this ) );
      endInput.keyup( _.bind(this.validateDate, this) );
   },
   unbindPanel: function(controlPanelDropdownEl){
      var startInput = $(controlPanelDropdownEl).find('[name="start_date"]');
      var endInput = $(controlPanelDropdownEl).find('[name="end_date"]');
      startInput.unbind();
      endInput.unbind();
   },
   validateDate: function(event){

      var dt = $(event.target).val();

      var carretPos = event.target.selectionStart -1;

      //Let the user use the backspace anywhere
      //in the string
      if(this.ignoreKeyCodes[event.keyCode]){
         return;
      }
      if( dt.match(/[^\d\-\:\s/]/) ){
         //Don't allow bad chars
         $(event.target).attr('value', dt.replace(/[^\d\-\:\s/]/, '') );
         return;
      }
      //collapse multiple spaces to one
      if( dt.match(/\s\s/g) ){
         $(event.target).attr('value', dt.replace(/\s\s/, ' ') );
         return;
      }
      //Let the user know when they have a bad date
      if( dt.match(/^\d\d\d\d\-\d\d\-\d\d\s\d\d\:\d\d\:\d\d$|^\d\d\d\d\-\d\d\-\d\d\s{0,}$/) ){
         $(this.badDateSel).addClass('hidden');
      }else{
         $(this.badDateSel).removeClass('hidden');
         $(this.serverResetSel).addClass('hidden');
      }
   },
   processData: function(dataObject, datatableObject, signals){

      /****************************
       * Carry out any data processing unique to the dview.
       *
       * Parameters:
       *    dataObject - Deserialized json from server.
       *    datatableObject - datatable.js object
       *    signals - Associative array of signals that the dview
       *              can receive/send
       * ***************************/
      if(dataObject.data.length >= 1 ){

         if(this.sorting[ this.adapter ]){
            datatableObject.aaSorting = this.sorting[this.adapter];
         }

         //Build column names for datatables.js
         for(i=0; i<dataObject['columns'].length; i++){
            var colName = dataObject['columns'][i];
            datatableObject.aoColumns.push({ "mDataProp":colName, "sTitle":colName });
         }

         for(var i=0; i<dataObject.data.length; i++){
            //Trying to avoid iterating over all columns here, some tables
            //have lots of columns that don't require any special formatting.
            //To account for this, formatter functions iterate over the limited
            //set of columns that need formatting.
            for( var formatCol in this.formatColumnMap ){
               if(this.formatColumnMap.hasOwnProperty(formatCol)){
                  if(dataObject.data[i][formatCol] != undefined){
                     this.formatColumnMap[formatCol](i, formatCol, dataObject);
                  }
               }
            }
            //Handling signal columns separately so we don't have to
            //hardcode the signals and map them to a specific handler function
            this._signalColumnFormatter(i, signals, dataObject);
         }
      }
   },
   processPanelClick: function(elId, dviewIndex){
      return;
   },
   setSelectionRange: function(input, selectionStart, selectionEnd){

      if(input.setSelectionRange){
         input.focus();
         input.setSelectionRange(selectionStart, selectionEnd);
      }else if(input.createTextRange){
         var range = input.createTextRange();
         range.collapse(true);
         range.moveEnd('character', selectionEnd);
         range.moveStart('character', selectionStart);
         range.select();
      }
   },
   _preTagFormatter: function(i, col, dataObject){
      dataObject.data[i][col] = '<pre>' + dataObject.data[i][col] + '</pre>';
   },
   _externalLinkFormatter: function(i, col, dataObject){
      var urlBase = "";
      if(col === 'revision'){
         var branch = "";
         if( DV_PAGE.refData != undefined ){
            if(DV_PAGE.refData.products[ dataObject.data[i][ 'product_id' ] ]){
               branch = DV_PAGE.refData.products[ dataObject.data[i][ 'product_id' ] ].branch
            }
         }
         urlBase = this.mercurialUrlBase.replace(/BRANCH/, branch.toLowerCase());
      }
      dataObject.data[i][col] = '<a target="_blank" href="' + urlBase +
                                   dataObject.data[i][col] + '">' + dataObject.data[i][col] + '</a>';
   },
   _escapeColumnFormatter: function(i, col, dataObject){
      //If the data going into the html table can contain html entities
      //install this formatter for the column
      if(dataObject.data[i][col] != undefined){
         dataObject.data[i][col] = DV_PAGE.escapeHtmlEntities(dataObject.data[i][col]);
      }
   },
   _signalColumnFormatter: function(i, signals, dataObject){
      for(var s in signals){
         if(signals.hasOwnProperty(s)){

            var eclass = 'dv-signal-' + s;
            if(dataObject.data[i][s] != undefined){

               if(typeof( dataObject.data[i][s] ) === 'number'){
                  dataObject.data[i][s] = '<div style="display:inline;"><a class="' + eclass + 
                                           '" href="#' + s + '">' + 
                                           DV_PAGE.escapeHtmlEntities(String(dataObject.data[i][s])) + 
                                           '</a></div>';
               }else{
                  var cmenu = "dv_table_contextmenu";
                  if(s === 'url'){
                     cmenu = "dv_url_contextmenu";
                  }else if(s === 'fatal_message'){
                     cmenu = "dv_fm_contextmenu";
                  }
                  dataObject.data[i][s] = '<div contextmenu="' + cmenu + 
                                        '" style="display:inline;"><a class="' + eclass + 
                                        '" href="#' + s + 
                                        '">' + DV_PAGE.escapeHtmlEntities(dataObject.data[i][s]) + 
                                        '</a></div>';
               }
            }
         }
      }
   }
});
var TestSelectorAdapter = new Class({

   Extends:DataViewAdapter,

   jQuery:'TestSelectorAdapter',

   initialize: function(selector, options){

      this.setOptions(options);
      this.parent(options);

      this.sortedTestCollection = this._sortObject(DV_PAGE.refData.test_collections);

      this.testCollectionToggleSel = '#dv_toggle_test_collection_c';
      this.advancedOptionsToggleSel = '#dv_toggle_advanced_options_c';
      this.dateRangeOptionsToggleSel = '#dv_toggle_date_range_c';

      this.testCollectionContainerSel = '#dv_add_test_collection_c';
      this.advancedOptionContainerSel = '#dv_advanced_options_c';
      this.dateRangeOptionContainerSel = '#dv_date_range_options_c';

      this.openIconClass = 'ui-icon-plusthick';
      this.closeIconClass = 'ui-icon-minusthick';

      this.addCollectionsSel = '#dv_add_test_collections_c';
      this.addBranchesSel = '#dv_add_branches_c';
      this.addTestsSel = '#dv_add_tests_c';
      this.addPlatformsSel = '#dv_add_platforms_c';

   },
   setControlPanelFields: function(controlPanelDropdownEl, data, dviewIndex){
  
      var dva = new DataViewAdapter();

      dva.setControlPanelFields(controlPanelDropdownEl, data, dviewIndex);

      //Set required ids
      this.testCollectionToggleId = this.view.getIdSelector(this.testCollectionToggleSel, 
                                                            dviewIndex);

      this.advancedOptionsToggleId = this.view.getIdSelector(this.advancedOptionsToggleSel, 
                                                             dviewIndex);

      this.dateRangeOptionsToggleId = this.view.getIdSelector(this.dateRangeOptionsToggleSel, 
                                                              dviewIndex);

      this.testCollectionContainerId = this.view.getIdSelector(this.testCollectionContainerSel,
                                                               dviewIndex);

      this.advancedOptionContainerId = this.view.getIdSelector(this.advancedOptionContainerSel,
                                                               dviewIndex);

      this.dateRangeOptionContainerId = this.view.getIdSelector(this.dateRangeOptionContainerSel,
                                                                dviewIndex);

      //unbind any pre-existing events
      $(this.testCollectionToggleId).unbind('click');
      $(this.advancedOptionsToggleId).unbind('click');
      $(this.dateRangeOptionsToggleId).unbind('click');

      //Bind onclick
      $(this.testCollectionToggleId).bind('click', _.bind(this._togglePanel, 
                                                          this, 
                                                          this.testCollectionToggleId, 
                                                          this.testCollectionContainerId));

      $(this.advancedOptionsToggleId).bind('click', _.bind(this._togglePanel, 
                                                           this, 
                                                           this.advancedOptionsToggleId, 
                                                           this.advancedOptionContainerId));

      $(this.dateRangeOptionsToggleId).bind('click', _.bind(this._togglePanel, 
                                                           this, 
                                                           this.dateRangeOptionsToggleId, 
                                                           this.dateRangeOptionContainerId));

      this._loadTestCollectionSelect(dviewIndex);
      this._loadBranchesSelect(dviewIndex);

      if(!_.isEmpty(data)){
         //this.clearPanel(controlPanelDropdownEl);
         var el = $(controlPanelDropdownEl).find('[name="' + data.signal + '"]');
         $(el).attr('value', DV_PAGE.unescapeForUrl(data.data));

         if(!_.isEmpty(data.date_range)){
            var startInput = $(controlPanelDropdownEl).find('[name="start_date"]');
            startInput.attr('value',  data.date_range.start_date );
            var endInput = $(controlPanelDropdownEl).find('[name="end_date"]');
            endInput.attr('value', data.date_range.end_date );
         }

      }else {

         var startInput = $(controlPanelDropdownEl).find('[name="start_date"]');
         var endInput = $(controlPanelDropdownEl).find('[name="end_date"]');

         //Only set the values to the default date range if both values
         //are undefined
         if( !startInput.val() && !endInput.val() ){ 
            startInput.attr('value',  $(this.startDateSel).val() );
            endInput.attr('value', $(this.endDateSel).val() );
         }
      }
   },
   processControlPanel: function(controlPanelSel, data, dviewIndex, visData){

      //Get test collection selections
      var params = "";
      var testCollectionSelect = this.view.getIdSelector(this.addCollectionsSel, 
                                                         dviewIndex);

      var collectionIds = [];
      this._getSelectedOptions(testCollectionSelect, collectionIds);

      if(data.data != undefined){
         return data.data;
      }

      //productIds, testIds, platformIds can be 
      //defined by either the control panel or the 
      //visualization.  The ids set by the visualization
      //are found in visData and are integrated here
      //with the control panel values... This is getting
      //ugly, need to think of a cleaner way to model this
      //behavior
      var productIds = [];
      var testIds = [];
      var platformIds = [];
      var testRunIds = [];
      var pageIds = [];

      this._loadVisData(visData, 
                        productIds, 
                        testIds, 
                        platformIds, 
                        testRunIds,
                        pageIds);

      for(var i=0; i<collectionIds.length; i++){
         if(DV_PAGE.refData.test_collections[ collectionIds[i] ]){
            var data = DV_PAGE.refData.test_collections[ collectionIds[i] ].data;
            for(var j=0; j<data.length; j++){
               productIds.push(data[j].product_id);
               testIds.push(data[j].test_id);
               platformIds.push(data[j].operating_system_id);
            }
         }
      }

      //Get branch selections
      var productSelect = this.view.getIdSelector(this.addBranchesSel, 
                                                  dviewIndex);

      var productIdString = this._getSelectedOptions(productSelect, productIds).join(',');
      if(productIdString){
         params = this._buildParams(params, 'product_ids', productIdString);
      }

      //Get test selections
      var testsSelect = this.view.getIdSelector(this.addTestsSel, 
                                                 dviewIndex);
      var testIdString = this._getSelectedOptions(testsSelect, testIds).join(',');
      if(testIdString){
         params = this._buildParams(params, 'test_ids', testIdString);
      }

      //Get platforms selections
      var platformsSelect = this.view.getIdSelector(this.addPlatformsSel, 
                                                    dviewIndex);
      var platformIdString = this._getSelectedOptions(platformsSelect, platformIds).join(',');
      if(platformIdString){
         params = this._buildParams(params, 'platform_ids', platformIdString);
      }

      var testRunIds = testRunIds.join(',');
      if(testRunIds){
         params = this._buildParams(params, 'test_run_id', testRunIds);
      }
      var pageIds = pageIds.join(',');
      if(testRunIds){
         params = this._buildParams(params, 'page_id', pageIds);
      }

      return params;

   },
   unbindPanel: function(controlPanelDropdownEl){

      var startInput = $(controlPanelDropdownEl).find('[name="start_date"]');
      var endInput = $(controlPanelDropdownEl).find('[name="end_date"]');

      startInput.unbind();
      endInput.unbind();

      $(this.testCollectionToggleId).unbind();
      $(this.advancedOptionsToggleId).unbind();
      $(this.dateRangeOptionsToggleId).unbind();

      var selectMenus = $(controlPanelDropdownEl).find('select');
      for(var i=0; i<selectMenus.length; i++){
         $(selectMenus[i]).unbind();
      }
   },
   _loadVisData: function(visData, 
                          productIds, 
                          testIds, 
                          platformIds, 
                          testRunIds,
                          pageIds){

      //REMOVE ON RELEASE
      if(visData === undefined){
         return;
      }
      for(var i=0; i<visData.length; i++){
         if( visData[i].product_id ){
            productIds.push( visData[i].product_id );
         }
         if( visData[i].test_id ){
            testIds.push( visData[i].test_id );
         }
         if( visData[i].operating_system_id ){
            platformIds.push( visData[i].operating_system_id );
         }
         if( visData[i].test_run_id ){
            testRunIds.push( visData[i].test_run_id );
         }
         if( visData[i].page_id ){
            pageIds.push( visData[i].page_id );
         }
      }
   },
   _togglePanel: function(iconId, panelId){

      if( $(iconId).hasClass(this.openIconClass) ){

         //Change icon
         $(iconId).removeClass(this.openIconClass);
         $(iconId).addClass(this.closeIconClass);

         //Open panel
         $(panelId).css('display', 'block');

      }else{
         //Change icon
         $(iconId).removeClass(this.closeIconClass);
         $(iconId).addClass(this.openIconClass);

         //Close panel
         $(panelId).css('display', 'none');
      }
   },
   _loadSelectMenu: function(id, name, value){
      var el = $('<option value="' + value + '">' + name + '</option>');
      $(id).append(el);
   },
   _loadTestCollectionSelect: function(dviewIndex){

      var selectTarget = this.view.getIdSelector(this.addCollectionsSel, 
                                                 dviewIndex);
      $(selectTarget).empty();

      for(var i=0; i<this.sortedTestCollection.values.length; i++){
         var name = this.sortedTestCollection.values[i];
         this._loadSelectMenu(selectTarget,
                              name,
                              this.sortedTestCollection.lookup[name]);
      }

   },
   _sortObject: function(o){

      var values = [];
      var idLookup = {};
      for (var key in o) {
         if (o.hasOwnProperty(key)) {
            values.push(o[key].name);
            idLookup[ o[key].name ] = key;
         }
      }
      values.sort();

      return { values:values, lookup:idLookup };
   },
   _loadBranchesSelect: function(dviewIndex){
      var selectTarget = this.view.getIdSelector(this.addBranchesSel, 
                                                 dviewIndex);
      $(selectTarget).empty();
      for(var id in DV_PAGE.refData.products){

         if(DV_PAGE.refData.products.hasOwnProperty(id)){

            var name = DV_PAGE.refData.products[id].product + ' ' +
                       DV_PAGE.refData.products[id].branch + ' ' +
                       DV_PAGE.refData.products[id].version;

            this._loadSelectMenu(selectTarget,
                                 name, 
                                 id);
         }
      }

      $(selectTarget).bind('click', _.bind(function(ev){ 
         var options = $(ev.currentTarget).find('option:selected');
         var productIds = {};
         for(var i=0; i<options.length; i++){
            productIds[ parseInt( $(options[i]).attr('value') ) ] = true;
         }

         this._loadTestSelect(dviewIndex, productIds);

         //Clear out the platforms when the branch changes
         var platformTarget = this.view.getIdSelector(this.addPlatformsSel, 
                                                      dviewIndex);
         $(platformTarget).empty();

      }, this));

   },
   _loadOsSelect: function(dviewIndex, testIds){
      var selectTarget = this.view.getIdSelector(this.addPlatformsSel, 
                                                 dviewIndex);
      $(selectTarget).empty();
      var osIds = {};
      for(var i=0; i<DV_PAGE.refData.product_test_os_map.length; i++){
         var mapObj = DV_PAGE.refData.product_test_os_map[i];
         if(testIds[ mapObj.test_id ]){
            osIds[ mapObj.operating_system_id ] = true;
         }
      }

      for(var id in DV_PAGE.refData.operating_systems){

         if(DV_PAGE.refData.operating_systems.hasOwnProperty(id)){
            var name = DV_PAGE.refData.operating_systems[id].name + ' ' +
                       DV_PAGE.refData.operating_systems[id].version;

            if(osIds[ id ]){
               this._loadSelectMenu(selectTarget,
                                    name, 
                                    id);
            }
         }
      }
   },
   _loadTestSelect: function(dviewIndex, productIds){
      var selectTarget = this.view.getIdSelector(this.addTestsSel, 
                                                 dviewIndex);
      $(selectTarget).empty();
      var testIds = {};
      for(var i=0; i<DV_PAGE.refData.product_test_os_map.length; i++){
         var mapObj = DV_PAGE.refData.product_test_os_map[i];
         if(productIds[ mapObj.product_id ]){
            testIds[ mapObj.test_id ] = true;
         }
      }
         
      for(var id in DV_PAGE.refData.tests){
         if(DV_PAGE.refData.tests.hasOwnProperty(id)){
            if(testIds[ id ]){
               this._loadSelectMenu(selectTarget,
                                    DV_PAGE.refData.tests[id].name,
                                    id);
            }
         }
      }
      $(selectTarget).bind('click', _.bind(function(ev){ 

         var options = $(ev.currentTarget).find('option:selected');
         var testIds = {};
         for(var i=0; i<options.length; i++){
            testIds[ parseInt( $(options[i]).attr('value') ) ] = true;
         }

         this._loadOsSelect(dviewIndex, testIds);

      }, this));
   },
   _getSelectedOptions: function(selectTarget, ids){

      var options = $(selectTarget).find('option');
      for(var i=0; i<options.length; i++){
         var selected = $(options[i]).attr('selected'); 
         if(selected){   
            ids.push($(options[i]).attr('value'));
         }
      }
      return _.uniq(ids, true);
   },
   _buildParams: function(params, key, parameter){
      if(params){
         params += '&' + key + '=' + parameter;
      }else{
         params += key + '=' + parameter;
      }
      return params;
   }


});
