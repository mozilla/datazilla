/******* 
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this file,
 * You can obtain one at http://mozilla.org/MPL/2.0/. 
 * *****/
var DataViewComponent = new Class({

    /********************************
     * DataViewComponent
     *
     *     This component encapsulates all of the functionality
     * of a single DataView.  The Data prefix on attribute or functions
     * is to help distinguish between the pane constructed in the 
     * user interface that constitutes a single functional component
     * and the View of MVC which is also used by the component.
     *     The component acts as both a public interface to component
     * functionality and a controller of it's own private View and Model
     * class.
     ********************************/
    Extends: Component,

    jQuery:'DataViewComponent',

    options: {
        dview_name:'',
        dview_index:0
    },

    initialize: function(selector, options){

        this.setOptions(options);

        this.parent(options);

        //This index is dynamically appended
        //to every id in a view clone.
        this.dviewIndex = this.options.dview_index;
        this.dviewParentIndex = this.options.dview_parent_index;
        this.parentWindowName = window.document.title;

        //Callback methods for button clicks
        this.buttonHandlers = { closetable:this.closeTable,
                                        openwindow:this.openWindow,
                                        refresh:this.refresh,
                                        help:this.help,
                                        signal_help:this.getDataHelp,
                                        newwindow:this.moveToNewWindow,
                                        increasesize:this.increaseSize,
                                        decreasesize:this.decreaseSize };

        //Adapters to manage idiosynchratic view behavior
        this.dataAdapters = new DataAdapterCollection();

        this.model = new DataViewModel('#DataViewModel', {dviewName:this.options.dview_name,
                                                                     dataAdapters:this.dataAdapters});

        this.visCollection = new VisualizationCollection('#VisualizationCollection', {});

        this.view = new DataViewView('#DataViewView', { vis_read_name:'Table'});

        //The parent view index, it will be defined when this window
        //was spawned from another.
        if(( (window.opener != undefined) && (window.opener.document != undefined) ) && 
            (this.dviewIndex === 0)){
            //get the parent dview index embedded in the page
            this.dviewParentIndex = this.view.getParentDataViewIndex();
            this.parentWindowName = window.opener.document.title;
        }

        //DataView events
        this.closeEvent = 'CLOSE_DATAVIEW';
        this.addDataViewEvent = 'ADD_DATAVIEW';
        this.signalEvent = 'SIGNAL_DATAVIEW';
        this.openCollectionEvent = 'OPEN_COLLECTION_DATAVIEW';
        this.processControlPanelEvent = 'PROCESS_CONTROL_PANEL';

        //Set up subscriptions
        this.subscriptionTargets = {};
        this.subscriptionTargets[this.processControlPanelEvent] = this.processControlPanel;
        this.subscriptionTargets[this.signalEvent] = this.signalHandler;

        //Register subscribers
        DV_PAGE.registerSubscribers(this.subscriptionTargets,
                                            this.view.allViewsContainerSel,
                                            this);

        //datatable.js object is stored in this attribute, it is set at runtime
        this.dataTable = undefined;

        //Look for signals embedded in the page to
        //initialize the control panel with
        this.signalData = this.getSignalDataFromPage();

        if(this.dviewIndex === 0){

            //Disable the close button so the user cannot
            //have a viewless page
            this.view.disableClose(this.dviewIndex);
        }

        //We could be a child in a new window, register listener
        //for cross window communication
        this.notifyDataViewCollection();

        //Get a new HTML clone for the 
        //view and initialize it.
        this.getDataViewClone();

        //Display parent/child relationship
        this.view.displayParentChild(this.dviewParentIndex, 
                                              this.dviewIndex, 
                                              this.parentWindowName);

        var defaultLoad = this.model.getDataViewAttribute('default_load')
        if( (defaultLoad === 1) || 
             ((this.dviewIndex === 0) && (this.signalData.signal != undefined)) ){
            //Select view and load the data
            this.view.displaySignalData('receive', this.signalData, this.dviewIndex);
            this.selectDataView();
        }else{
            var dviewReadName = this.model.getDataViewAttribute('read_name');

            this.view.displayDataViewName(this.dviewIndex, dviewReadName);
            this.setControlPanelEv();

            this.view.showNoDataMessage(this.dviewIndex, 'sendsignal');
        }

    },
    /****************
     *PUBLIC INTERFACE
     ****************/
    showTableSpinner: function(){
        this.view.showTableSpinner(this.dviewIndex);
    },
    closeMenu: function(){
        this.view.closeMenu();
    },
    getColumnData: function(column, columnFilter){

        var columnData = [];
        var data = this.dataTable.fnGetData();
        for(var i=0; i<data.length; i++){
            if(data[i][column]){
                var cell = data[i][column];
                if(columnFilter){
                    cell = columnFilter(data[i][column]);
                }
                columnData.push(cell);
            }
        }
        return columnData;
    },
    notifyDataViewCollection: function(){

        if( (window.opener != undefined) && (window.opener.document != undefined) ){
            //If we have an opener we're a child on a new page
            window.opener.DV_PAGE.DataViewCollection.loadNewChildWindow(window);
            //Register listener for signals from parent
            window.addEventListener('message', _.bind(this.processWindowSignal, this));
        }

    },
    processWindowSignal: function(event){

        var data = this.validateMessageData(event);
        if( (window.opener != undefined) && (window.opener.document != undefined) ){
            if(!_.isEmpty(data)){
                //Make sure the window/view sender are the appropriate parents
                if((data.window_sender === window.opener.document.title) && 
                    (this.dviewParentIndex === data.parent_dview_index)){

                    //Let listener know this is a window message
                    data['window_message'] = true;
                    $(this.view.allViewsContainerSel).trigger(this.signalEvent, data);

                }
            }
        }
    },
    validateMessageData: function(event){

        var safeData = {};
        var dataObject = JSON.parse(event.data);
        var targetOrigin = DV_PAGE.getTargetOrigin();

        //Validate the origin is correct
        if(targetOrigin === event.origin){

            //Validate that we have the required fields, any window
            //could send a message
            if( (dataObject.data != undefined) &&
                 (dataObject.window_sender != undefined) &&
                 (dataObject.signal != undefined) ){

                //Yer all clear kid!
                safeData = dataObject;
            }
        }

        return safeData;
    },
    destroy: function(){

        //Delete the view from the DOM
        this.view.removeDataView(this.dviewIndex);

        //Unbind local events
        var paginationSel = this.view.getTablePaginationSel(this.dviewIndex);
        $(paginationSel).unbind();

        //Get rid of any events assigned with live
        if(this.dataTable != undefined){
            this.dataTable.die();
            //Call table destructor
            this.dataTable.fnDestroy();
        }

        //Unbind custom events
        DV_PAGE.unbindSubscribers(this.subscriptionTargets,
                                         this.view.allViewsContainerSel);

        //This should be done programmatically but not sure
        //if delete will work without explicit attribute reference.
        //Need to do some research...
        delete(this.subscriptionTargets);
        delete(this.dviewIndex);
        delete(this.buttonHandlers);
        delete(this.model);
        delete(this.view);
        delete(this.visCollection);
        delete(this.dataAdapters);
        delete(this.closeEvent);
        delete(this.addDataViewEvent);
        delete(this.processControlPanelEvent);
        delete(this.signalEvent);
        delete(this.subscriptionTargets);
        delete(this.signalData);
        delete(this.dataTable);
    },
    selectDataView: function(item){

        var dviewName = "";
        if(item != undefined){
            //Called from callback
            dviewName = item.href.replace(/^.*?\#/, '');
        }else{
            //Called directly, use the dviewHash
            dviewName = this.model.getDataViewAttribute('name');
        }

        //Protect against user selecting a non-anchor region of the menu
        if(dviewName === ""){
            return;
        }

        //Check for any page targets
        var ptarget = this.model.getDataViewPageTarget(dviewName);
        if(ptarget != undefined){
            //View uses a pages target not the web service
            //send user to page
            ptarget = ptarget.replace('HASH', '#');

            window.open(ptarget);

            return false;
        }

        //Set data for new view
        this.model.setDataViewHash(dviewName);

        //Set the visualization default
        var charts = this.model.getDataViewAttribute('charts');
        this.setVisualizationDefault(charts);

        //Check if we have a collection
        var collection = this.model.getDataViewAttribute('collection')

        if( collection != undefined ){
            var data = { parent_dview_index:this.dviewIndex,
                             collection:collection,
                             display_type:DV_PAGE.ConnectionsComponent.getDisplayType() };

            //Set the name to the 0 collection element
            dviewName = collection[0].dview;

            //Set data for the new collection view
            this.model.setDataViewHash(dviewName);

            //Fire event to load the rest of the collection
            $(this.view.allViewsContainerSel).trigger(this.openCollectionEvent, data);

            return false;

        }

        var dviewReadName = this.model.getDataViewAttribute('read_name');

        //Display new view's name
        this.view.displayDataViewName(this.dviewIndex, dviewReadName);

        this.view.showTableSpinner(this.dviewIndex);

        //Set up control panel, this must be done
        //in the selectDataView method to account for
        //unique control panel/dview relationships
        this.setControlPanelEv();

        //Display signal data
        //this.view.displaySignalData('', this.signalData, this.dviewIndex);
        var adapterName = this.model.getDataViewAttribute('data_adapter');
        var a = this.dataAdapters.getAdapter(adapterName);
        var params = "";
        if(this.signalData.signal != undefined){
            params += 'start_date=' + this.signalData.date_range.start_date +
                         '&end_date=' + this.signalData.date_range.end_date + '&' +
                         this.signalData.signal + '=' + this.signalData.data;
        }else{
            params = a.getDefaultParams();
        }
        this.model.getDataViewData(dviewName,
                                         this,
                                         this.initializeDataView,
                                         params,
                                         this.fnError);
    },

    /***************
     * CUSTOM EVENT HANDLERS
     *
     * Custom events are defined in the constructor and
     * can be triggered from any other component.  All 
     * custom events are triggered on the '#dv_view_container' 
     * div.  This gives subscribers a single place to register.
     ***************/
    processControlPanel: function(data){

        var dviewIndex = parseInt(data.dview_index);

        //Since this is an event listener on the main view container
        //we need to confirm that the click event matches this DataView's 
        //index.
        if((dviewIndex === this.dviewIndex) || (data.signal != undefined)){
            var controlPanelDropdownSel = this.view.getIdSelector(this.view.controlPanelDropdownSel, 
                                                                                 this.dviewIndex);
            /*********************
             * TODO:
             *
             * The relationship between the VisualizationAdapter and
             * the DataAdapter is getting a bit fuzzy here.  Need to re-think
             * the OOP design to handle data view signal data that lives in the
             * visualization only:
             *
             * data view-> dataset and signal->signal fields->signal field data
             *            1-> many                 1->many          1->many
             *
             * This is very different than the bughunter data and is not 
             * appropriately handled in the object model.
             * ********************/
            //Get data from the visualization
            var visData = this.visCollection.getVisData(this.visName);
            var adapterName = this.model.getDataViewAttribute('data_adapter');
            var a = this.dataAdapters.getAdapter(adapterName);

            //Combine control panel selections with the visualization data
            var params = "";
            params = a.processControlPanel(controlPanelDropdownSel, 
                                                     data, 
                                                     this.dviewIndex, 
                                                     visData);
            this.updateSignalDateRange();

            this.view.showTableSpinner(this.dviewIndex);

            this.model.getDataViewData(this.model.getDataViewAttribute('name'),
                                             this, 
                                             this.initializeDataView,
                                             params,
                                             this.fnError);
        }
    },
    signalHandler: function(data){
        //This view sent the signal
        if( data.parent_dview_index === this.dviewIndex ){
            //Display signal sent label
            this.view.displaySignalData('send', data, this.dviewIndex);
        }

        //Determine if this view can process the signal
        var processSignal = false;
        if(data.window_message === true){

            //message was sent from another window and has already been validated for receiving
            processSignal = true;

        }else if( (data.parent_dview_index != this.dviewIndex) && 
                     (this.dviewParentIndex === data.parent_dview_index) ){

            //signal was sent from inside page, make sure it was not this view that sent it
            //and that the signal was sent from this view's parent
            processSignal = true;

        }

        if(this.model === undefined){
            //NOTE: this.model should never be undefined.  This is a hack to 
            //        handle when a dview has been deleted by the user.  When
            //        a view is deleted the destroy method should remove all event 
            //        listeners.  However, the destroy method fails to remove signal
            //        listeners. I think this is an artifact of using _.bind but need
            //        to look into this more.
            processSignal = false;
        }

        if(processSignal){

            var signals = this.model.getDataViewAttribute('signals');

            if(data.window_message != true){
                //Get parent view index
                var parentIndex = DV_PAGE.DataViewCollection.getDataViewParent(this.dviewIndex);
                if( parentIndex != data.parent_dview_index ){
                    //signal sender is not the parent, ignore
                    return;
                }
            }

            //data view does not understand the signal
            if(signals[ data.signal ] != 1){
                return;
            }

            this.signalData = data;

            var controlPanelDropdownSel = this.view.getIdSelector(this.view.controlPanelDropdownSel, 
                                                                                    this.dviewIndex);

            //Display the signal data
            this.view.displaySignalData('receive', this.signalData, this.dviewIndex);
            var adapterName = this.model.getDataViewAttribute('data_adapter');
            var a = this.dataAdapters.getAdapter(adapterName);
            //Pre-fill any fields
            a.setControlPanelFields(controlPanelDropdownSel, 
                                            this.signalData, 
                                            this.dviewIndex);

            var controlPanelDropdownSel = this.view.getIdSelector(this.view.controlPanelDropdownSel, 
                                                                                    this.dviewIndex);
            this.processControlPanel(this.signalData);
        }
    },

    /********************
     *DATAVIEW LOCAL EVENT REGISTRATION
     *
     * Local events in this case are events that 
     * have a single listener that is the DataView itself.
     ********************/
    registerDataViewEvents: function(){

        //Set up component events
        this.setMenuEv();
        this.setButtonEv();

    },
    setMenuEv: function(){

        $.ajax(this.view.navMenuHtmlUrl, { 

            accepts:'text/html',
            dataType:'html',

            success: _.bind(function(data){

                var navMenuSel = this.view.getIdSelector(this.view.navMenuSel, this.dviewIndex);

                $(navMenuSel).menu({ 
                    content: data,
                    flyOut: true,
                    showSpeed: 150,
                    callback:{ method:this.selectDataView, 
                                  context:this }
                });
            }, this) //end bind
        });
    },
    setControlPanelEv: function(){

        var controlPanel = this.model.getDataViewAttribute('control_panel');
        var controlPanelUrl = this.view.controlPanelHtmlUrl + controlPanel;

        $.ajax(controlPanelUrl, { 
            accepts:'text/html',
            dataType:'html',
            success: _.bind( this._setControlPanelCb, this )
        });
    },
    setVisEv: function(){

        var dviewName = this.model.getDataViewAttribute('name');

        //Get chart types for dview
        var charts = this.model.getDataViewAttribute('charts');

        //Get anchor id and ul id for view clone
        var visualizationSel = this.view.getIdSelector(this.view.visualizationSel, this.dviewIndex);
        var visMenuSel = this.view.getIdSelector(this.view.visMenuSel, this.dviewIndex);

        //Set the chart types
        this.view.setDataViewChartTypes(charts, visMenuSel);
        $(visualizationSel).menu({
            content: $(visMenuSel).html(),
            showSpeed: 50,
            callback: { method:this.setVisualization, context:this }
        });
    },
    setVisualizationDefault: function(charts, visName, readName){

        if( (charts != undefined) && (charts.length > 0) ){

            for(var i=0; i<charts.length; i++){
                if(parseInt(charts[i]['default']) === 1){
                    this.visName = charts[i]['name'];
                    this.view.visReadName = charts[i]['read_name'];
                }
            }

        }else{

            this.visName = visName;
            if( this.visName === "" ){
                this.visName = "table";
            }
            this.view.visReadName = readName;
            if( this.view.visReadName === "" ){
                this.view.visReadName = "Table";
            }

        }
    },
    setButtonEv: function(){

        var topBarSel = this.view.getIdSelector(this.view.topBarSel, this.dviewIndex);
        var sel = '[id$="bt_c_' + this.dviewIndex + '"]';
        var topBarAnchors = $(topBarSel).find(sel);
        for(var i=0; i<topBarAnchors.length; i++){
            var a = topBarAnchors[i];
            $(a).bind('click', {}, _.bind( function(event){
                //Get the href of the anchor
                var buttonType = "";
                if(event.target.tagName === 'SPAN'){
                    var p = $(event.target).parent();

                    var signalHelpSel = this.view.getIdSelector(this.view.signalHelpBtSel, this.dviewIndex);
                    if($(event.target).attr('id')){ 
                        buttonType = 'signal_help';
                    }else{
                        buttonType = $(p).attr('href').replace('#', '');
                    }
                }else { 
                    buttonType = $(event.target).attr('href').replace('#', '');
                }

                if( _.isFunction(this.buttonHandlers[ buttonType ]) ){
                    _.bind(this.buttonHandlers[ buttonType ], this)(); 
                }else{
                    console.log("Component Error: No button handler for " + buttonType);
                }
                event.stopPropagation();
            }, this));
        }
    },
    /************************
     *DATAVIEW PREPARATION METHODS
     ************************/
    getDataViewClone: function(){

        //Clone a new view
        this.view.cloneDataView(this.dviewIndex);

        //Show the spinner
        this.view.showSpinner(this.dviewIndex);

        //Register view events
        this.registerDataViewEvents();
    },

    initializeDataView: function(data, textStatus, jqXHR){

        this.data = data;

        if(data.aoColumns.length > 0){
            //Load the data into the table
            var tableSel = this.view.getIdSelector(this.view.tableSel, this.dviewIndex);

            if(this.tableCreated === true){
                //Remove any events that were assigned with live
                $(tableSel).die();
                //destroy the table
                this.dataTable.fnClearTable();
                this.dataTable.fnDestroy();
            }

            //Get a new clone of the table
            this.view.getNewTableClone(this.dviewIndex, tableSel);

            //Set the chart types
            this.setVisEv();

            //Set the visualization default
            if(this.visName === undefined){
                var charts = this.model.getDataViewAttribute('charts');
                this.setVisualizationDefault(charts);
            }

            //Load the table data
            this.dataTable = $(tableSel).dataTable( data );

            //Set up signal handling
            this.setDataTableSignals();

            this.tableCreated = true;

            var dviewReadName = this.model.getDataViewAttribute('read_name');

            //Let everyone see the lovely view!
            this.view.showDataView(this.dviewIndex, dviewReadName);

            //The table is loaded and drawn first when it is hidden
            //this causes the column/row alignment to get off.  Redraw
            //the table after its display is set to visible to reset
            //alignment.
            this.dataTable.fnDraw();
            this.dataTable.fnAdjustColumnSizing();

            this.view.setHeight(tableSel, this.view.minScrollPanelSize);

            this.setVisualization();

        }else{
            this.view.showNoDataMessage(this.dviewIndex);
        } 
    },
    getSignalDataFromPage: function(){

        var signals = this.model.getDataViewAttribute('signals');

        var adapterName = this.model.getDataViewAttribute('data_adapter');
        var a = this.dataAdapters.getAdapter(adapterName);

        var signalData = {};
        signalData['date_range'] = a.getDateRangeParams('', this.signalData);

        if(signals != undefined){

            for(var signal in signals){
                if(signals.hasOwnProperty(signal)){


                    var signalDataSel = this.view.signalBaseSel + signal;
                    var data = $( signalDataSel ).val();

                    if(data != undefined){

                        signalData['signal'] = signal;
                        signalData['data'] = decodeURIComponent(data);

                        //Remove signal to prevent all new dviews from using
                        //it as a default
                        $( signalDataSel ).remove();
                    }
                }
            }
        }

        return signalData;
    },
    updateSignalDateRange: function(){

        var controlPanelDropdownSel = this.view.getIdSelector(this.view.controlPanelDropdownSel, 
                                                                                this.dviewIndex);
        var adapterName = this.model.getDataViewAttribute('data_adapter');
        var a = this.dataAdapters.getAdapter(adapterName);
        var dateRange = a.getDateRangeParams(controlPanelDropdownSel, this.signalData);
        this.signalData['date_range'] = dateRange;

    },
    setDataTableSignals: function(){

        //if the table is scrolled make sure we close any open menus
        $(this.view.tableScrollClassSel).bind('scroll', _.bind(function(e){
            if(this.view != undefined){
                this.view.closeMenu();
            }
        }, this));

        //Catch click events on the datatable
        $(this.dataTable).live("click", _.bind( this._dataTableClickHandler, this));

    },
    _dataTableClickHandler: function(event){

        //close any open menus
        this.view.closeMenu();

        event.stopPropagation();

        //If user selected an anchor in the main cell content
        //selectedTrEl will be a tr element
        //var selectedTrEl = $(event.target).parent().parent().parent();
        var selectedTrEl = $(event.target).closest('tr');

        //Make sure a table row was retrieved
        if( $(selectedTrEl).is('tr') ){

            this.view.selectTableRow( selectedTrEl );

            var href = $(event.target).attr('href');
            if(href != undefined){

                href = href.replace(/\#/, '');

                var adapterName = this.model.getDataViewAttribute('data_adapter');
                var a = this.dataAdapters.getAdapter(adapterName);
                var targetData = DV_PAGE.escapeForUrl($(event.target).text());


                var controlPanelDropdownSel = this.view.getIdSelector(this.view.controlPanelDropdownSel, 
                                                                                        this.dviewIndex);
                var dateRange = a.getDateRangeParams(controlPanelDropdownSel, this.signalData);

                var signalData = { parent_dview_index:this.dviewIndex,
                                         data:targetData,
                                         date_range:dateRange,
                                         signal:href };

                $(this.view.allViewsContainerSel).trigger(this.signalEvent, signalData);
            }
        }
    },
    /**************
     *BUTTON CLICK HANDLERS
     **************/
    closeTable: function(){
        this.view.closeMenu();
        //disable button if we are the main view
        if(this.dviewIndex != 0){
            $(this.view.allViewsContainerSel).trigger( this.closeEvent, { dview_index:this.dviewIndex } ); 
        }
    },
    moveToNewWindow: function(){

        this.view.closeMenu();
        if(this.dviewIndex != 0){

            //Get the dateRange
            var controlPanelDropdownSel = this.view.getIdSelector(this.view.controlPanelDropdownSel, 
                                                                                    this.dviewIndex);
            var adapterName = this.model.getDataViewAttribute('data_adapter');
            var a = this.dataAdapters.getAdapter(adapterName);
            var params = a.processControlPanel(controlPanelDropdownSel, this.signalData);

            var dviewName = this.model.getDataViewAttribute('name');

            //Build the data object for the event
            var data = { selected_dview:dviewName,
                             parent_dview_index:this.dviewParentIndex,
                             dview_index:this.dviewIndex,
                             display_type:'page',
                             params:params };

            $(this.view.allViewsContainerSel).trigger(this.addDataViewEvent, data);
            $(this.view.allViewsContainerSel).trigger( this.closeEvent, { dview_index:this.dviewIndex } ); 
            
        }
    },
    openWindow: function(){

        this.view.closeMenu();
        var signals = this.model.getDataViewAttribute('signals');
        DV_PAGE.ConnectionsComponent.setDataViewIndex(this.dviewIndex);
        DV_PAGE.ConnectionsComponent.open('open', signals);

    },
    refresh: function(){

        this.view.closeMenu();

        data = { dview_index:this.dviewIndex }; 

        this.processControlPanel(data);

    },
    help: function(){

        this.view.closeMenu();
        var src = "/" + DV_PAGE.project + "/help";
        var dialogHtml = this.view.getHelpModal(src);

        $(dialogHtml).dialog('open');
        return false;
    },
    getDataHelp: function(){

        this.view.closeMenu();
        var name = this.model.getDataViewAttribute('name')
        var src = "/" + DV_PAGE.project + "/help#" + name;
        var dialogHtml = this.view.getHelpModal(src);
        $(dialogHtml).dialog('open');

        return false;
    },
    increaseSize: function(){

        this.view.closeMenu();
        var newHeight = this.view.changeViewHeight(this.dviewIndex, 'increase');
        this.dataTable.fnSettings().oScroll.sY = newHeight + 'px';
    },
    decreaseSize: function(){

        this.view.closeMenu();
        var newHeight = this.view.changeViewHeight(this.dviewIndex, 'decrease');
        this.dataTable.fnSettings().oScroll.sY = newHeight + 'px';
    },
    setVisualization: function(item){

        var charts = this.model.getDataViewAttribute('charts');

        //item is defined and menuToggle is set to true when the user 
        //toggles the Visualization from the menu
        var menuToggle = false;
        if(item){
            var visName = $(item).attr('href').replace('#', '');
            if(visName != undefined){
                this.visName = visName;
            }
            menuToggle = true;
        }

        this._setVisReadName(charts);

        var dviewReadName = this.model.getDataViewAttribute('read_name');

        this.view.displayDataViewName(this.dviewIndex, dviewReadName);

        var datatableWrapperSel = this.view.getIdSelector(this.view.tableSel, this.dviewIndex) + 
                                          this.view.wrapperSuffix;

        var visContainerSel = this.view.getIdSelector(this.view.visContainerSel, this.dviewIndex);

        var singleViewSel = this.view.getIdSelector(this.view.singleViewContainerSel, this.dviewIndex);

        if(this.visName != 'table'){
            
            var detailSelectors = this.view.getVisDetailSelectors(this.dviewIndex);

            var controlPanelDropdownSel = this.view.getIdSelector(this.view.controlPanelDropdownSel, 
                                                                                    this.dviewIndex);
            var adapterName = this.model.getDataViewAttribute('data_adapter');
            var a = this.dataAdapters.getAdapter(adapterName);
            var dateRange = a.getDateRangeParams(controlPanelDropdownSel, this.signalData);

            var signalData = { parent_dview_index:this.dviewIndex,
                                     data:"",
                                     date_range:dateRange,
                                     color:"",
                                     read_names:[],
                                     label:"",
                                     signal:"" };

            var displayData = { vis_name:this.visName,
                                      data:this.dataTable.fnGetData(),
                                      selectors:detailSelectors,
                                      //empty signalData structure that the visualization
                                      //can use to construct a new event
                                      signal_data:signalData,
                                      //signalData that the view received
                                      incoming_signal_data:this.signalData };

            this.visCollection.display(displayData, menuToggle);
        }

        this.view.closeMenu();

        this.view.displayVisualization(datatableWrapperSel, 
                                                 visContainerSel, 
                                                 singleViewSel, 
                                                 this.visName);
    },
     
    /*************
     *MENU CALLBACK METHODS
     *************/
    fnError: function(data, textStatus, jqXHR){
        var messageText = 'Ohhh no, something has gone horribly wrong! ';
        messageText += ' HTTP status:' + data.status + ', ' + textStatus +
        ', ' + data.statusText;

        this.view.showNoDataMessage(this.dviewIndex, 'error', messageText); 
    },
     _setControlPanelCb: function(data){

        var controlPanelSel = this.view.getIdSelector(this.view.controlPanelSel, this.dviewIndex);
        var controlPanelId = this.view.getId(this.view.controlPanelSel, this.dviewIndex);

        //Remove existing menu from DOM
        this.view.removeControlPanel(this.dviewIndex);

        //Set up ids
        var htmlEl = this.view.initializeControlPanel(data, this.dviewIndex);

        $(controlPanelSel).menu({ 
            content: htmlEl.html(),
            showSpeed: 150,
            width: this.view.controlPanelWidth,

            onOpen: _.bind(this._controlPanelOnOpen, this),

            onClose: _.bind( this._controlPanelOnClose, this),

            //This clickHandler prevents the form from closing when it's
            //clicked for data input.  
            clickHandler:_.bind( this._controlPanelClickHandler, this)
        });
    },
    _controlPanelOnOpen: function(event){

        //Make sure we don't have any extra keydown event bindings
        $(document).unbind('keydown');

        //Populate the control panel fields with
        //any signal data
        var controlPanelDropdownSel = this.view.getIdSelector(this.view.controlPanelDropdownSel, 
                                                                                this.dviewIndex);

        var adapterName = this.model.getDataViewAttribute('data_adapter');

        var a = this.dataAdapters.getAdapter(adapterName);

        a.setControlPanelFields(controlPanelDropdownSel,
                                        this.signalData,
                                        this.dviewIndex);

        //Capture keydown and look for enter/return press
        $(document).keydown( _.bind( this._processControlPanelKeyPress, this ) );
    },
    _controlPanelOnClose: function(event){
        //Update the signal data when the menu is closed to make 
        //sure we get any modification to the date range
        var controlPanelDropdownSel = this.view.getIdSelector(this.view.controlPanelDropdownSel, 
                                                                                this.dviewIndex);
        var adapterName = this.model.getDataViewAttribute('data_adapter');
        var a = this.dataAdapters.getAdapter(adapterName);
        a.unbindPanel(controlPanelDropdownSel);

        var dateRange = a.getDateRangeParams(controlPanelDropdownSel, {});

        if(this.signalData){
            this.signalData['date_range'] = dateRange;
        }

        //This is really dangerous, it will clear all keydown events
        //assigned at the document level... which really should not be 
        //any.  When passing a function to unbind it fails probably because
        //_.bind() is used for context management... Ughhhh
        $(document).unbind('keydown');

    },
    _controlPanelClickHandler: function(event){

        var controlPanelBtId = this.view.getId(this.view.controlPanelBtSel, 
                                                            this.dviewIndex);

        var controlPanelClearBtId = this.view.getId(this.view.controlPanelClearBtSel, 
                                                                  this.dviewIndex);

        var controlPanelDropdownSel = this.view.getIdSelector(this.view.controlPanelDropdownSel, 
                                                                                this.dviewIndex);

        var elId = $(event.target).attr('id');

        //This enables control panel's with checkboxes
        var adapterName = this.model.getDataViewAttribute('data_adapter');
        var a = this.dataAdapters.getAdapter(adapterName);
        a.processPanelClick(elId, this.dviewIndex);

        if( elId === controlPanelBtId ){
            //close menu
            this.view.closeMenu();
            //fire event
            $(this.view.allViewsContainerSel).trigger( this.processControlPanelEvent, 
                                                                  { dview_index:this.dviewIndex }); 
        }else if(elId === controlPanelClearBtId){
            a.clearPanel(controlPanelDropdownSel);
        }
        event.stopPropagation();
    },
    _processControlPanelKeyPress: function(event){
        //If the user presses enter/return simulate form submission
        if(event.keyCode === 13){
            //close menu
            this.view.closeMenu();
            //fire event
            $(this.view.allViewsContainerSel).trigger( this.processControlPanelEvent, 
                                                                  { dview_index:this.dviewIndex }); 
        }
    },

    _setVisReadName: function(charts){
        for(var i=0; i<charts.length; i++){
            if(charts[i].name === this.visName){
                this.view.visReadName = charts[i].read_name;
                break;
            }
        }
    }
});
var DataViewView = new Class({

    /**************************
     * DataView manages all direct DOM manipulation
     * for the component.
     *************************/

    Extends:View,

    jQuery:'DataViewView',

    initialize: function(selctor, options){

        this.setOptions(options);

        this.parent(options);

        //HTML for navigation menu, control panel, and help
        this.navMenuHtmlUrl = '/media/html/nav_menu.html';
        this.controlPanelHtmlUrl = '/media/html/control_panels/';
        this.helpHtmlUrl = '/help/';

        this.controlPanelWidth = 525;
        this.minVisContainerHeight = 640;

        //Scrolling params
        this.minScrollPanelSize = 200;
        this.defaultScrollPanelSize = 500;
        this.tableScrollClassSel = '.dataTables_scrollBody';

        //Main View Container
        this.allViewsContainerSel = '#dv_view_container';

        //Cloned Containers
        this.viewWrapperSel = '#dv_view_wrapper_c';
        this.singleViewContainerSel = '#dv_view_c';
        this.dvDefaultHeight = $(this.singleViewContainerSel).css('height');
        this.dvMinHeight = 85;

        //table wrapper suffix
        this.wrapperSuffix = '_wrapper';

        //Spinners
        this.spinnerSel = '#dv_spinner_c';
        this.tableSpinnerSel = '#dv_table_spinner_c';
        this.tableNoDataSel = '#dv_table_nodata_c';

        //Data table
        this.tableSel = '#dv_tview_c';
        //Data table pagination container
        this.tablePaginationSel = '#dv_tview_c_DATAVIEW_INDEX_paginate';

        //Top bar selectors
        this.topBarSel = '#dv_topbar_c';
        this.navMenuSel = '#dv_nav_menu_c';
        this.controlPanelSel = '#dv_control_panel_c';
        this.visualizationSel = '#dv_visualization_c';
        this.visMenuSel = '#dv_vis_menu_c';
        this.topBarTitleSel = '#dv_view_title_c';

        this.scrollBodyClassSel = 'dataTables_scrollBody';

        //Close button selector
        this.closeButtonSel = '#dv_closetable_bt_c';
        this.newWindowButtonSel = '#dv_newwindow_bt_c';

        //Control panel ids
        this.controlPanelBtSel = '#dv_cp_load_view_c';
        this.controlPanelClearBtSel = '#dv_cp_clear_c';
        this.controlPanelDropdownSel = '#dv_cp_dropdown_c';

        //Signal display ids
        this.signalDataSentDisplaySel = '#dv_signal_data_sent_c';
        this.signalDataReceivedDisplaySel = '#dv_signal_data_received_c';
        this.signalDateRangeDisplaySel = '#dv_signal_date_range_c';
        this.signalHelpBtSel = '#dv_signal_help_bt_c';
        this.maxSignalDataLength = 50;

        //Parent/Child relationship display
        this.parentIndexDisplaySel = '#dv_parent_display_c';
        this.viewIndexDisplaySel = '#dv_view_display_c';
        this.parentDataViewIndexSel = '#dv_parent_dview_index';

        //Visualization containers
        this.visContainerSel = '#dv_vis_container_c';
        this.graphContainerSel = '#dv_vis_graph_c';
        this.graphDetailsContainerSel = '#dv_vis_details_c';
        this.visLiCloneSel = '#dv_vis_li_clone';

        this.visDetailSelectors = { graph_detail:'#dv_vis_graph_detail_c',
                                             graph_detail_two:'#dv_vis_graph_detail_two_c',
                                             graph_detail_container:'#dv_vis_graph_container_c',
                                             hover_detail:'#dv_hover_detail_c',
                                             click_detail:'#dv_click_detail_c'};

        this.visReadName = options.vis_read_name;

        //Spacer div between dviews
        this.spacerSel = "#dv_spacer_c";
        this.tableSpacerHeight = 10;
        this.visSpacerHeight = 550;

        //Clone id selector, finds all elements with an id attribute ending in _c
        this.cloneIdSelector = '*[id$="_c"]';

        //The current selected row element in a table, set at runtime
        this.selectedTrEl = undefined;

        //Signal base id
        this.signalBaseSel = '#dv_post_';

        //Messages
        this.nodataMessage = 'No data available.';
        this.sendSignalMessage = 'Select a link in the parent view to send a signal.';
    },
    getTablePaginationSel: function(dviewIndex){
        return this.tablePaginationSel.replace('DATAVIEW_INDEX', dviewIndex);
    },
    /****************************
     *DATAVIEW PREPARATION METHODS
     ****************************/
    cloneDataView: function(dviewIndex){

        //Clone single view container and append to the main container
        var viewWrapperEl = $(this.viewWrapperSel).clone();

        //Set up new dviewIndex based id
        var viewWrapperId = this.getId(this.viewWrapperSel, dviewIndex);
        $(viewWrapperEl).attr('id', viewWrapperId);

        $(this.allViewsContainerSel).append(viewWrapperEl);

        //Set the ids on the new clone
        this.setCloneIds(viewWrapperEl, dviewIndex);

    },
    setCloneIds: function(containerEl, dviewIndex){

        //find all elements with an id attribute ending in _c
        var cloneIdElements = $(containerEl).find(this.cloneIdSelector);

        for(var i=0; i<cloneIdElements.length; i++){
            var id = $(cloneIdElements[i]).attr('id'); 
            //Append the index to the id to make id unique
            $(cloneIdElements[i]).attr('id', this.getId(id, dviewIndex));
        }

        //Check the element itself
        var containerId = $(containerEl).attr('id');
        if(!(containerId === undefined)){
            if(containerId.search(/_c$/) > -1){
                $(containerEl).attr('id', this.getId(containerId, dviewIndex));
            }
        }

        return containerEl;
    },
    getNewTableClone: function(dviewIndex, tableSel){
        //hide the table
        $(tableSel).fadeOut();
        //remove from DOM 
        $(tableSel).remove();
        //get a new clone
        var tableEl = $(this.tableSel).clone();
        //reset id
        $(tableEl).attr('id', this.getId(this.tableSel, dviewIndex));
        //Get the topbar div to append to
        var topBarSel = this.getIdSelector(this.topBarSel, dviewIndex);
        //load the new clone
        $(topBarSel).append( tableEl );
    },
    initializeControlPanel: function(html, dviewIndex){
        var cpSel = this.getIdSelector(this.controlPanelDropdownSel, dviewIndex);
        var el = this.setCloneIds($(html), dviewIndex);
        return el;
    },
    setDataViewChartTypes: function(charts, bhVisMenuSel){

        var menuChildren = $(bhVisMenuSel).children();
        var liCloneEl = $(this.visLiCloneSel).get(0);

        for(var i=0; i<menuChildren.length; i++){
            var liEl = menuChildren[i]; 
            if( !$(liEl).attr('id') ){
                //Pre-existing li from another view type, delete it
                $(liEl).remove();
            }
        }

        if( _.isElement( liCloneEl ) ){

            for(var i=0; i < charts.length; i++){

                var c = charts[i];

                //clone the li
                var newLiEl = $(liCloneEl).clone();
                newLiEl.attr('id', '');

                //get anchor and set attributes and show the new li
                var anchor = $(newLiEl).find('a');
                $(anchor).attr('href', '#' + c.name);
                $(anchor).text(c.read_name);
                $(bhVisMenuSel).append(newLiEl);
                newLiEl.css('display', 'block');
            }

        }else{
            console.log("html error: the element:" + bhVisMenuSel + " needs a <li></li> to clone!");
        }
    },
    removeControlPanel: function(dviewIndex){

        /*******************
         * Beware Holy Hackery Ahead!
         *
         * fg.menu maintains a global array with menu
         * objects containing each menu that it has positioned.
         * In order to completely remove a positioned menu the 
         * following steps need to be carried out:
         *     
         *     1.) Unbind all events from the control panel anchor
         *     2.) Remove the menu object from allUIMenus
         *     3.) Remove the menu and its parent positioning div
         *          from the DOM.
         *     4.) If the user has not opened the control panel
         *          and switches views the previous dropdown menu
         *          will not have the positioning div but will still
         *          need to be removed. Remove it from the DOM using 
         *          its element id.
         *
         * NOTE: Clearly we are using fg.menu in a way that it 
         *         was not intended to be used.  A better approach
         *         would be a clean destructor implementation for menu 
         *         objects that live entirely in fg.menu but this will 
         *         require some significant changes to fg.menu.
         ********************/
        var controlPanelSel = this.getIdSelector(this.controlPanelSel, 
                                                              dviewIndex);
        $(controlPanelSel).unbind();

        //Remove menu from global array of menus
        var controlPanelDropdownId = this.getId(this.controlPanelDropdownSel, 
                                                             dviewIndex);
        for(var i=0; i<allUIMenus.length; i++){
            if(allUIMenus[i].menuExists){
                if(allUIMenus[i].elementId === controlPanelDropdownId){
                    //close the menu
                    allUIMenus[i].kill();
                    //remove it from allUIMenus
                    allUIMenus = _.without( allUIMenus, allUIMenus[i] );
                }
            }
        }

        //Remove click event listeners
        $(controlPanelDropdownId).unbind('click');

        /**********************
         * fg.menu wraps a div with the class positionHelper around
         * the menu to help with absolute positioning.  If we just remove
         * the dropdown menu without removing the positionHelper all
         * hell breaks loose because the positionHelper divs accumulate.  
         * This bit of hackery removes the container around the dropdown.
         * Ugh... I feel dirty.
         **********************/
        var sel = '[id="' + controlPanelDropdownId + '"]';
        var pD = $('.positionHelper').find(sel);
        var positionHelper = pD.parent().parent();
        $(positionHelper).remove();

    },
    /************************
     *DATAVIEW MODIFICATION METHODS
     ************************/
    displayParentChild: function(parentIndex, dviewIndex, parentWindowName){

        var parentIndexDisplaySel = this.getIdSelector(this.parentIndexDisplaySel, dviewIndex);
        var viewIndexDisplaySel = this.getIdSelector(this.viewIndexDisplaySel, dviewIndex);

        var parentText = parentWindowName;
        var viewText = parseInt(dviewIndex) + 1; 

        if(parentIndex >= 0){
            parentText += ", View " + (parseInt(parentIndex) + 1);
        }

        $(parentIndexDisplaySel).text(parentText);
        $(viewIndexDisplaySel).text(viewText);

    },
    disableClose: function(dviewIndex){
        var closeButtonSel = this.getIdSelector(this.closeButtonSel, dviewIndex);
        $(closeButtonSel).addClass("ui-state-disabled");

        var newWindowButtonSel = this.getIdSelector(this.newWindowButtonSel, dviewIndex);
        $(newWindowButtonSel).addClass("ui-state-disabled");
    },
    selectTableRow: function( selectedTrEl ){

        //Remove class on existing selection
        if(this.selectedTrEl){
            $(this.selectedTrEl).removeClass('row_selected');
        }

        //Get the row
        this.selectedTrEl = selectedTrEl;

        var trClass = $(this.selectedTrEl).attr('class');

        //Give it the selected class
        $(this.selectedTrEl).addClass('row_selected');

    },
    removeDataView: function(dviewIndex){
        var wrapperSel = this.getIdSelector(this.viewWrapperSel, dviewIndex);
        $(wrapperSel).remove(); 
    },
    changeViewHeight: function(dviewIndex, direction){

        //scrollable table area
        var scrollContainerEl = this.getTableScrollContainer(dviewIndex);
        //scrollable visualization area
        var visContainerSel = this.getIdSelector(this.visContainerSel, dviewIndex);

        var h = parseInt( $(scrollContainerEl).css('height') );

        if(direction === 'decrease'){

            h = h - this.minScrollPanelSize;
            //Set the minimum
            if(h < this.minScrollPanelSize){
                h = this.minScrollPanelSize;
            }

        }else {
            h = h + this.minScrollPanelSize;
        }

        var hPix = h + 'px';
        $(scrollContainerEl).css('height', hPix);
        $(visContainerSel).css('height', hPix);

        return hPix;
    },
    setHeight: function(tableSel, targetHeight){
        var scrollBody = $(tableSel).parent();
        var h = parseInt( $(scrollBody).css('height') );
        if( h < targetHeight ){
            var newHeight = this.minScrollPanelSize + 'px';
            $(scrollBody).css('height', newHeight);
        }
    },
    /*******************
     * GET METHODS
     *******************/
    getParentDataViewIndex: function(){
        return parseInt($(this.parentDataViewIndexSel).val());
    },
    getFilterSel: function(dviewIndex){
        return '#dv_tview_c_' + dviewIndex + '_filter';
    },
    getTableScrollContainer: function(dviewIndex){
        var tableSel = this.getIdSelector(this.tableSel, dviewIndex);
        return $(tableSel).parent(); 
    },
    getHelpModal: function(src){

        var helpIframe = '<div><iframe class="dv-help-frame ui-corner-all" src="' + src + '"></iframe></div>';
        var dialogHtml = $(helpIframe);

        $(dialogHtml).dialog({
            autoOpen: false,
            width: 600,
            height: 800,
            modal: true,
            title: "Data View Help"
         });

         return dialogHtml;
    },
    /*******************
     *TOGGLE METHODS
     *******************/
    displayVisualization: function(datatableWrapperSel, visContainerSel, singleViewSel, visName){

        if(visName === 'table'){

            $(datatableWrapperSel).css('display', 'block');
            $(visContainerSel).css('display', 'none');

            $(singleViewSel).css('height', this.dvDefaultHeight);

        }else {

            //This is required so the visualization panel does not get pushed 
            //down by the container
            $(singleViewSel).css('height', this.dvMinHeight);

            $(datatableWrapperSel).css('display', 'none');

            $(visContainerSel).css('height', this.minVisContainerHeight);
            $(visContainerSel).css('display', 'block');
        }
    },
    getVisDetailSelectors: function(dviewIndex){

        var detailSelectors = {};
        var graphContainerSel = this.getIdSelector(this.graphContainerSel, dviewIndex);
        var graphDetailsContainerSel = this.getIdSelector(this.graphDetailsContainerSel, dviewIndex);

        for(var detailKey in this.visDetailSelectors){
            if(this.visDetailSelectors.hasOwnProperty(detailKey)){
                var detailSelector = this.getIdSelector(this.visDetailSelectors[detailKey], dviewIndex);
                detailSelectors[detailKey] = detailSelector;
            }
        }
        detailSelectors.detail_container = graphDetailsContainerSel;
        detailSelectors.graph_container = graphContainerSel;

        return detailSelectors;
    },
    displayDataViewName: function(dviewIndex, dviewReadName){
        var topbarTitleSel = this.getIdSelector(this.topBarTitleSel, dviewIndex);
        $(topbarTitleSel).text(dviewReadName + ', ' + this.visReadName);
    },
    displaySignalData: function(direction, signalData, dviewIndex){

        var signalDateRangeDisplaySel = this.getIdSelector(this.signalDateRangeDisplaySel, dviewIndex);

        //Show data range sent if we have one
        if(signalData.date_range){
            var dateRange = signalData.date_range.start_date + ' to ' + signalData.date_range.end_date;
            $(signalDateRangeDisplaySel).text(dateRange); 
        }

        //Show signal type and associated data
        if(signalData.data != undefined){
            var data = signalData.label;
            if(!data){
                data = signalData.data;
            }
            var data = DV_PAGE.unescapeForUrl( data );
            var displayData = data;
            if(signalData.data && signalData.signal){
                if(data.length >= this.maxSignalDataLength){
                    displayData = data.substring(0, this.maxSignalDataLength - 3) + '...';
                }
            }
            if(direction === 'receive'){
                var signalDataReceivedDisplaySel = this.getIdSelector(this.signalDataReceivedDisplaySel, dviewIndex);
                $(signalDataReceivedDisplaySel).text(displayData);
                $(signalDataReceivedDisplaySel).attr('title', data);
            }else if(direction === 'send'){
                var signalDataSentDisplaySel = this.getIdSelector(this.signalDataSentDisplaySel, dviewIndex);
                $(signalDataSentDisplaySel).text(displayData);
                $(signalDataSentDisplaySel).attr('title', data);
            }
        }
    },
    showNoDataMessage: function(dviewIndex, messageType, messageText){

        //Hide main pane spinner
        this.hideSpinner(dviewIndex);

        //Hide the table
        var tableSel = this.getIdSelector(this.tableSel, dviewIndex);
        $(tableSel).addClass('hidden');

        //Hide the spinner
        var spinnerSel = this.getIdSelector(this.tableSpinnerSel, dviewIndex);
        $(spinnerSel).css('display', 'none');
        
        //Show the single dview container
        var singleViewSel = this.getIdSelector(this.singleViewContainerSel, dviewIndex);
        $(singleViewSel).removeClass('hidden');


        //Show top bar container
        var topBarSel = this.getIdSelector(this.topBarSel, dviewIndex);
        $(topBarSel).removeClass('hidden');

        //Show message
        var noDataSel = this.getIdSelector(this.tableNoDataSel, 
                                                      dviewIndex);

        var message = this.nodataMessage;
        if(messageType === 'sendsignal'){
            message = this.sendSignalMessage;
        }else if(messageType === 'error'){
            message = messageText;
        }
        $(noDataSel).text(message);
        $(noDataSel).css('display', 'block');

    },
    closeMenu: function(){
        /*************
         *This method calls the kill() method of
         *an fg.menu object to close the menu explicitly.
         *************/
        for(var i=0; i<allUIMenus.length; i++){
            if(allUIMenus[i].menuExists){
                allUIMenus[i].kill();
            }
        }
    },
    showDataView: function(dviewIndex, dviewReadName){

        //Show the topbar and table, they still won't be visible
        //at this point because their container div is hidden but
        //they will be ready for the fadeIn()
        var topBarSel = this.getIdSelector(this.topBarSel, dviewIndex);
        $(topBarSel).removeClass('hidden');
        var tableSel = this.getIdSelector(this.tableSel, dviewIndex);
        $(tableSel).removeClass('hidden');

        this.displayDataViewName(dviewIndex, dviewReadName);

        if(dviewIndex === 0){
            //Disable the close button and move to new window button so the user cannot
            //have a viewless page
            this.disableClose(dviewIndex);
        }

        //Hide the spinner
        this.hideSpinner(dviewIndex);
        this.hideTableSpinner(dviewIndex);

        //Hide the no data message
        var noDataSel = this.getIdSelector(this.tableNoDataSel, 
                                                      dviewIndex);
        $(noDataSel).css('display', 'none');

        //If the spinner has been shown the viewWrapper is likely visible
        //but lets make sure in case caller did not call showSpinner()
        var viewWrapperSel = this.getIdSelector(this.viewWrapperSel, dviewIndex);
        $(viewWrapperSel).css('display', 'block');

        //Show the container
        var singleViewContainerSel = this.getIdSelector(this.singleViewContainerSel, dviewIndex);
        $(singleViewContainerSel).fadeIn();

    },
    showSpinner: function(dviewIndex){
        //Make sure the wrapper is visible
        var viewWrapperSel = this.getIdSelector(this.viewWrapperSel, dviewIndex);
        $(viewWrapperSel).removeClass('hidden');

        //Hide visualization
        var visContainerSel = this.getIdSelector(this.visContainerSel, dviewIndex);
        $(visContainerSel).css('display', 'none');

        //Show spinner
        var spinnerSel = this.getIdSelector(this.spinnerSel, dviewIndex);
        $(spinnerSel).css('display', 'block');
    },
    showTableSpinner: function(dviewIndex){

        var noDataSel = this.getIdSelector(this.tableNoDataSel, 
                                                      dviewIndex);
        $(noDataSel).css('display', 'none');

        var tableSel = this.getIdSelector(this.tableSel, dviewIndex) + this.wrapperSuffix;
        $(tableSel).css('display', 'none');

        //Hide visualization
        var visContainerSel = this.getIdSelector(this.visContainerSel, dviewIndex);
        $(visContainerSel).css('display', 'none');

        //Make sure we're the default size, if were displaying a
        //visualization the container size maybe less than the default
        var singleViewSel = this.getIdSelector(this.singleViewContainerSel, dviewIndex);
        $(singleViewSel).css('height', this.dvDefaultHeight);

        //Show spinner
        var spinnerSel = this.getIdSelector(this.tableSpinnerSel, dviewIndex);
        $(spinnerSel).css('display', 'block');
    },
    hideSpinner: function(dviewIndex){
        //Needs to be display:none; so the view container doesn't get
        //pushed down.
        var spinnerSel = this.getIdSelector(this.spinnerSel, dviewIndex);
        $(spinnerSel).css('display', 'none');
    },
    hideTableSpinner: function(dviewIndex){
        var spinnerSel = this.getIdSelector(this.tableSpinnerSel, dviewIndex);
        $(spinnerSel).css('display', 'none');

        var tableSel = this.getIdSelector(this.tableSel, dviewIndex) + this.wrapperSuffix;
        $(tableSel).css('display', 'block');
    }
});
var DataViewModel = new Class({

    /****************************
     * DataViewModel manages data structures and server 
     * side data retrieval.
     ****************************/
    Extends:View,

    jQuery:'DataViewModel',

    initialize: function(selector, options){

        this.setOptions(options);

        this.parent(options);

        //enable ajax POST with CDRF Token
        //this.modelAjaxSend();

        this.dataAdapters = options.dataAdapters;

        //Options for this view from views.json
        this.dviewHash = {};
        this.setDataViewHash(this.options.dviewName);
        this.apiLocation = "/" + DV_PAGE.project + "/api/";
        this.dateRangeLocation = "/" + DV_PAGE.project + "/api/get_date_range";

        //This is set from any incoming view data
        //to whatever the final range was.  If the
        //range provided by the UI is invalid the server 
        //will reset it.
        this.start_date = "";
        this.end_date = "";
    },
    /***************
     *GET METHODS
     ***************/
    getDataViewAttribute: function(attr){
        return this.dviewHash[attr];
    },
    getDataViewData: function(dviewName, context, fnSuccess, params, fnError){

        var url = this.apiLocation + dviewName;

        //Check for default data
        var serviceUrl = this.getDataViewAttribute('service_url');
        var data;
        if(serviceUrl != undefined){
            url = serviceUrl;
        }else{
            if(params != undefined){
                data = params;
            }else if(_.isString(this.dviewHash['default_params'])){
                data = this.dviewHash['default_params'];
            }
        }

        jQuery.ajax( url, { accepts:'application/json',
                                  dataType:'json',
                                  cache:false,
                                  type:'GET',
                                  data:data,
                                  context:context,
                                  error:fnError,
                                  success:fnSuccess,
                                  dataFilter:_.bind(this.datatableAdapter, this) });

    },
    getDataViewPageTarget: function(dviewName){
        if (DV_PAGE.navLookup[dviewName]){
            return DV_PAGE.navLookup[dviewName]['page_target'];
        }
    },
    /*****************
     *SET METHODS
     *****************/
    setDataViewHash: function(dviewName){
        if (DV_PAGE.navLookup[dviewName]){
            this.dviewHash = DV_PAGE.navLookup[dviewName];
        }else{
            console.log('view.json error: The view name, ' + dviewName + ' was not found!');
        }
    },
    datatableAdapter: function(data, type){
        /*************
         * Adapt webservice data to datatable structure
         *************/
        //When JSON.parse() is used here jQuery fails to pass the
        //data returned to the success function ref.  This is why
        //jQuery.parseJSON is being used instead.  Not sure why this
        //occurs.
        var dataObject = jQuery.parseJSON( data );

        //Set the date range
        this.start_date = dataObject.start_date;
        this.end_date = dataObject.end_date;

        //enable dview hidden columns
        var hiddenColumns = this.getDataViewAttribute('hidden_columns');
        var aTargets = [];
        for(var col in hiddenColumns){
            if(hiddenColumns.hasOwnProperty(col)){
                aTargets.push(parseInt(hiddenColumns[col]));
            }
        }

        //NOTE: datatableObject cannot be an attribute of the
        //        model instance because it is unique to different 
        //        views.
        var datatableObject = { bJQueryUI: true,
                                        sPaginationType: "full_numbers",
                                        bPaginate: true,
                                        sScrollY:"500px",
                                        bScrollCollapse:true,
                                        sScrollX:"100%",

                                        //Hide these columns in initial display
                                        aoColumnDefs:[ 
                                            { bVisible: false, aTargets:aTargets }
                                        ],

                                        //Double, Double Toil and Trouble
                                        //see http://www.datatables.net/usage/options sDom for an
                                        //explanation of the follow line
                                        sDom:'<"H"lfr>tC<"F"ip>',

                                        bScrollAutoCss: false,
                                        bRetrieve:true,
                                        //Treat search string as regexes
                                        oSearch:{ sSearch:"", bRegex:true },
                                        xScrollInner:true,
                                        iDisplayLength:100,
                                        aLengthMenu:[[25, 50, 100, 500, 1000], [25, 50, 100, 500, 1000]],
                                        aaData:dataObject.data,
                                        aoColumns:[],

                                        oColVis:{
                                            buttonText: "&nbsp;",
                                            bRestore: true,
                                            sAlign: "left",
                                            sSize: "css"
                                        }
                                    };

        var signals = this.getDataViewAttribute('signals');
        //Get a data adapter to process the data.  This allows
        //individual dviews to process the data according to 
        //their requirements
        var adapterName = this.getDataViewAttribute('data_adapter');
        var a = this.dataAdapters.getAdapter(adapterName);
        a.processData(dataObject, datatableObject, signals);

        return JSON.stringify(datatableObject);
    }
});
