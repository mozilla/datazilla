/******* 
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this file,
 * You can obtain one at http://mozilla.org/MPL/2.0/. 
 * *****/
var DataViewCollection = new Class({

    /***************************
     * DataViewCollection
     *
     *  Manages a collection of DataViews.  Uses a private model
     *  and view class for support.
     ***************************/
    Extends:Options,

    jQuery:'DataViewCollection',

    initialize: function(selector, options){

        this.setOptions(options);

        this.model = new DataViewCollectionModel('#DataViewCollectionModel', {});
        this.view = new DataViewCollectionView('#DataViewCollectionView', {});

        this.dviewIndex = undefined;
 
        //Get the view marked as default in json structure
        this.defaultDataViewName = this.model.getDefaultDataView();

        this.subscriptionTargets = { CLOSE_DATAVIEW:this.closeDataView,
                                     ADD_DATAVIEW:this.addDataView,
                                     SIGNAL_DATAVIEW:this.sendSignalToChildWindows,
                                     OPEN_COLLECTION_DATAVIEW:this.openDataViewCollection };

        DV_PAGE.registerSubscribers(this.subscriptionTargets, 
                                            this.view.allViewsContainerSel,
                                            this);

        //reset column widths when window resizes
        $(window).resize( _.bind( this.resizeWindow, this ) );

    },
    openDataViewCollection: function(data){

        var parentToIndexMap = {};

        //force parent to be the first dview
        data.parent_dview_index = 0;

        var indexTargets = this.model.getAllDataViewIndexes();
        //Remove all dviews
        for(var i=0; i<indexTargets.length; i++){
            this.closeDataView({ dview_index:indexTargets[i] });
        }

        for(var i=0; i < data.collection.length; i++){

            var dviewChild = data.collection[i].dview;
            var dviewParent = data.collection[i].parent;

            var dviewData = {  selected_dview:dviewChild,
                                      display_type:'pane',
                                      parent_dview_index:parentToIndexMap[dviewParent] };
            if( i === 0 ){
                //Collection is set as the default item to display
                var newIndex = this.addDataView(dviewData);
                parentToIndexMap[dviewChild] = newIndex;
            }else{
                var newIndex = this.addDataView(dviewData);
                parentToIndexMap[dviewChild] = newIndex;
            }
        }
    },
    resizeWindow: function(event){
        for(var i=0; i < this.model.dviewCollection.length; i++){
            if( this.model.dviewCollection[i].dataTable != undefined ){
                this.model.dviewCollection[i].dataTable.fnAdjustColumnSizing();
            }
        }
    },
    getDataViewsBySignal: function(signal){
        return this.model.getDataViewsBySignal(signal);
    },
    getDataViewsBySignalHash: function(signals){
        return this.model.getDataViewsBySignalHash(signals);
    },
    getAllDataViewNames: function(){
        return this.model.getAllDataViewNames();
    },
    getDataViewParent: function(childIndex){
        return this.model.dviewRelationships[ childIndex ]['parent'];
    },
    addDataView: function(data){
        var dviewName = data.selected_dview;

        if(!this.model.hasDataView(dviewName)){
            dviewName = this.model.getDefaultDataView();
        }

        var dviewHash = DV_PAGE.navLookup[dviewName];

        //View has no pane version and can only be launched
        //as a new page
        if(dviewHash && (dviewHash.page_target != undefined)){
            //Check for any page targets
            var url = dviewHash.page_target.replace('HASH', '#');
            window.open(url);
            return false;
        }

        //Open new page for dview
        if(data.display_type === 'page'){

            //NOTE:THis will be required if a data view needs to maintain
            //state when it's detached.  Leaving this in as a reminder for now.
            //The data structure urlData would be passed to submitPostForm and used
            //for data aquisition.
            //
            //var dview = this.model.getDataView(data.dview_index);
            //var urlData = dview.visCollection.getUrlData( dview.visName );

            this.view.submitPostForm(this.model.newViewUrl, data);

        }else {

            if(dviewHash.collection != undefined){
                //view is a collection let openDataViewCollection handle it
                var dataForCollection = { parent_dview_index:undefined,
                                                  collection:dviewHash.collection,
                                                  display_type:'pane' };
                this.openDataViewCollection(dataForCollection);
                return false;
            }

            var dviewIndex = this.model.getNewDataViewIndex();

            var dviewComponent = new DataViewComponent('#dviewComponent',
                               { dview_name:dviewName,
                                 dview_parent_index:data.parent_dview_index,
                                 dview_index:dviewIndex });

            this.model.addParentChildRelationship(data.parent_dview_index,
                                                  dviewIndex);

            this.model.addDataView(dviewComponent, dviewIndex);

            return dviewIndex;
        }
    },
    closeDataView: function(data){
        var dview = this.model.getDataView(data.dview_index);
        if( dview != undefined ){
            dview.destroy();
            this.model.removeDataView(data.dview_index);
        }
    },
    loadNewChildWindow: function(childWindow){
        this.model.loadNewChildWindow(childWindow);
    },
    sendSignalToChildWindows: function(data){
        //Make sure the message was not sent from another window
        if(data.window_message === undefined){
            //Send message to child windows and include which
            //window sent the message
            data['window_sender'] = document.title;

            var targetOrigin = DV_PAGE.getTargetOrigin();

            for(var i=0; i<this.model.childWindows.length; i++){
                this.model.childWindows[i].postMessage(JSON.stringify(data),
                                                       targetOrigin);
            }
        }
    }
});
var DataViewCollectionView = new Class({

    Extends:View,

    jQuery:'DataViewCollectionView',

    initialize: function(selector, options){

        this.parent(options);

        this.urlBase = '/' + DV_PAGE.project + '/';
        this.allViewsContainerSel = '#dv_view_container';
        this.resubmitUrlDialogSel = '#dv_resubmit_urls';
        this.resubmitUrlTextareaSel = '#dv_urls_container';
        this.resubmitCommentsSel = '#dv_resubmit_comments';
        this.resubmitSuccessSel = '#dv_resubmission_summary';
        this.resubmitSuccessMessageSel = '#dv_resubmission_message';

    },
    submitPostForm: function(newViewUrl, data){

        var params = data.params;
        var selectedView = data.selected_dview;
        var parentDataviewIndex = data.parent_dview_index;

        /*****************
         * Note: Ran into some issues submitting the form
         * dynamically using jquery so using straight js here
         * instead.
         * ***************/

        //Create a form that will open a new page when submitted
        var form = document.createElement("form");
        form.setAttribute("method", "post");
        form.setAttribute("action", this.urlBase + '#' + selectedView);
        form.setAttribute("target", "_blank");

        var signals = DV_PAGE.navLookup[selectedView]['signals'];

        var hiddenFields = this.loadSignalDataInPage(params, 
                                                                    parentDataviewIndex, 
                                                                    signals);

        for(var i=0; i < hiddenFields.length; i++){
            form.appendChild(hiddenFields[i]);
        }

        document.body.appendChild(form);

        var t = form.submit();

        //Finished with the form, remove from DOM
        $(form).remove();
    },
    loadSignalDataInPage: function(params, parentDataviewIndex, signals){

        var hiddenFields = [];

        if((signals != undefined) && (params != undefined)){
            for(var sig in signals){
                if(signals.hasOwnProperty(sig)){
                
                    //TODO: This commented out block might be a possible approach to
                    //maintaining state when a panel is detached.  Going to first see if
                    //this is required functionality, if not it should be removed.
                    if(sig === 'test_run_data'){

                        ///var signalHiddenField = document.createElement("input");

                        //Load any signals in the params
                        //signalHiddenField.setAttribute('type', 'hidden');
                        //signalHiddenField.setAttribute('name', sig);
                        //signalHiddenField.setAttribute('value', encodeURIComponent( urlData ));
                        //hiddenFields.push(signalHiddenField);

                    }else{

                        var match = params.split(sig + '=');

                        //Make sure we have a match for a name/value pair
                        if((match != null) && (match.length >= 2)){

                            var signalHiddenField = document.createElement("input");

                            //Load any signals in the params
                            signalHiddenField.setAttribute('type', 'hidden');
                            signalHiddenField.setAttribute('name', sig);
                            signalHiddenField.setAttribute('value', encodeURIComponent(match[1]));
                            hiddenFields.push(signalHiddenField);

                        }
                    }
                    //Load the date range
                    var dateMatch = match[0].replace(/&$/, '').split('&');
                    if((dateMatch != null) && (dateMatch.length >= 2)){
                        for(var i=0; i < dateMatch.length; i++){
                            
                            var dateNameValue = dateMatch[i].split('=');
                            var signalHiddenField = document.createElement("input");
                            signalHiddenField.setAttribute('type', 'hidden');
                            signalHiddenField.setAttribute('name', dateNameValue[0]);
                            signalHiddenField.setAttribute('value', dateNameValue[1]);
                            hiddenFields.push(signalHiddenField);
                        }
                    }
                }
            }
        }

        //Add the index of the parent view
        var parentHiddenField = document.createElement("input");
        parentHiddenField.setAttribute('type', 'hidden');
        parentHiddenField.setAttribute('name', 'dv_parent_dview_index');
        parentHiddenField.setAttribute('value', parentDataviewIndex);
        hiddenFields.push(parentHiddenField);

        return hiddenFields;
    },
    loadUrls: function(urls){

        $(this.resubmitUrlTextareaSel).empty();
        var seen = {};
        var count = 1;
        var uniqueUrls = [];
        for(var i=0; i<urls.length; i++){
            //Don't load duplicate urls
            if( seen[ urls[i] ] != true){
                uniqueUrls.push(urls[i]);
                var row = '<tr><td>' + count + '</td>' + '<td>' + urls[i] + '</td></tr>';
                $(this.resubmitUrlTextareaSel).append( $(row) );
                seen[ urls[i] ] = true;
                count++;
            }
        }

        return uniqueUrls;
    }
});

var DataViewCollectionModel = new Class({

    Extends:Model,

    jQuery:'DataViewCollectionModel',

    initialize: function(selector, options){

        this.parent(options);

        this.newViewUrl = '/' + DV_PAGE.project;
        this.urlResubmissionUrl = '/dataviews/api/resubmit/';

        //An object acting like an associative array that holds
        //all views
        this.dviewCollection = {};

        //The length of dviewCollection
        this.length = 0;

        /******
         * This data structure maintains the parent/child relationships
         * for all views a user has created
         * 
         *     { dviewIndex: { parent:parent dviewIndex,
         *                            children: { child dviewIndex1 .. dviewIndexn } }
         *
         * ****/
        this.dviewRelationships = {};

        //List of children window objects on different tabs.
        //Used to manage cross tab communication.
        this.childWindows = [];

    },
    addParentChildRelationship: function(parentIndex, childIndex){

        //Has the parent already been entered?
        if(this.dviewRelationships[parentIndex]){
            //Add the child index to children
            this.dviewRelationships[parentIndex]['children'][childIndex] = 1;
            this.dviewRelationships[childIndex] = { 'parent':parentIndex, 'children':{} };
        }else if( (parentIndex === undefined) && (childIndex === 0)){
            //First view
            this.dviewRelationships[childIndex] = { 'parent':undefined, 'children':{} }; 
        }
    },
    getLength: function(){
        return this.length;
    },
    getDataView: function(dviewIndex){
        if( this.dviewCollection[ dviewIndex ] != undefined ){
          return this.dviewCollection[dviewIndex]; 
        }
    },
    getAllDataViewIndexes: function(){
        var indexTargets = [];
        for(var dviewIndex in this.dviewCollection){
            if(this.dviewCollection.hasOwnProperty(dviewIndex)){
                indexTargets.push(dviewIndex);
            }
        }
        return indexTargets;
    },
    getNewDataViewIndex: function(){
        for(var i=0; i<this.length; i++){
            //Use any view indexes that have been removed
            if(this.dviewCollection[i] === undefined){
                return i;
            }
        }
        return this.length;
    },
    getDefaultDataView: function(){
        for( var dviewName in  DV_PAGE.navLookup ){
            if(DV_PAGE.navLookup.hasOwnProperty(dviewName)){
                if (_.isNumber( DV_PAGE.navLookup[dviewName]['default'] )){
                    return dviewName;
                }
            }
        }
    },
    getAllDataViewNames: function(){

        var mapReturn = _.map( _.keys( DV_PAGE.navLookup ), function(key){ 
            return { name:key, read_name:DV_PAGE.navLookup[key]['read_name'] };
        });

        return mapReturn;
    },
    getDataViewsBySignal: function(signal){
        var dviews = [];
        for( var dviewName in  DV_PAGE.navLookup ){
            if(DV_PAGE.navLookup.hasOwnProperty(dviewName)){
                if (DV_PAGE.navLookup[dviewName]['send_only'] != undefined){
                    //Some views can only send signals not receive them, exclude from list
                    continue;
                }
                if (DV_PAGE.navLookup[dviewName]['signals'] != undefined){
                    if (DV_PAGE.navLookup[dviewName]['signals'][signal] != undefined){
                        dviews.push(DV_PAGE.navLookup[dviewName]);
                    }
                }
            }
        }
        return dviews;
    },
    getDataViewsBySignalHash: function(signals){
        var dviews = [];
        for( var dviewName in  DV_PAGE.navLookup ){
            if(DV_PAGE.navLookup.hasOwnProperty(dviewName)){
                if (DV_PAGE.navLookup[dviewName]['send_only'] != undefined){
                    //Some views can only send signals not receive them, exclude from list
                    continue;
                }
                if (DV_PAGE.navLookup[dviewName]['signals'] != undefined){
                    for(var signal in signals){
                        if(signals.hasOwnProperty(signal)){
                            if (DV_PAGE.navLookup[dviewName]['signals'][signal] != undefined){
                                dviews.push(DV_PAGE.navLookup[dviewName]);
                                //We only need one match to include the signla
                                break;
                            }
                        }
                    }
                }
            }
        }
        return dviews;
    },
    hasDataView: function(dviewName){
        if(!(DV_PAGE.navLookup[dviewName] === undefined)){
            return true;
        }else{
            return false;
        }
    },
    addDataView: function(dview, dviewIndex){
        this.dviewCollection[ dviewIndex ] = dview;
        this.length++;
    },
    removeDataView: function(dviewIndex){

        if( this.dviewRelationships[dviewIndex] != undefined ){
            var parentIndex = this.dviewRelationships[dviewIndex]['parent'];
            if( this.dviewRelationships[parentIndex] != undefined ){
                //Remove this child from parent's children
                delete(this.dviewRelationships[parentIndex]['children'][dviewIndex]);
            }
            //Remove this dview
            delete(this.dviewRelationships[dviewIndex]);
            delete(this.dviewCollection[dviewIndex]);

            this.length--;
        }
    },
    loadNewChildWindow: function(newWin){
        this.childWindows.push(newWin);
    }
});
