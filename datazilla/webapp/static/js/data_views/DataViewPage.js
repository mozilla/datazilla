/******* 
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this file,
 * You can obtain one at http://mozilla.org/MPL/2.0/. 
 * *****/
var DV_PAGE;

var DataViewPage = new Class( {

    Extends: Page,

    jQuery:'DataViewPage',

    initialize: function(selector, options){

        this.parent(options);
        this.allViewsContainerSel = '#dv_view_container';
        this.addDataViewEvent = 'ADD_DATAVIEW';
        this.openCollectionEvent = 'OPEN_COLLECTION_DATAVIEW';

        /**********
         * DataView page names are managed with two keys in localStorage.
         *
         * localStorage[this.localStorageKey] = { 1:true, 2:true, 3:true ... Any number of bughunter pages }
         * localStorage[this.pageCountName] = Total number of items in localStorage[this.localStorageKey]
         *
         * Anytime a new page is opened, the page number will be set to any missing number in 
         * localStorage[this.localStorageKey], or if no number is available the next sequential 
         * number is used.
         *
         * ********/
        this.localStorageKey = 'DV_PAGES';
        this.windowBaseName = "Perf-o-Matic ";
        this.pageCountName = 'DV_PAGE_COUNT';

        //Add new page
        this.windowCount = 0;
        var winName = this.getWindowName(this.windowBaseName);
        document.title = winName;

        //Make sure we adjust the page count variable in localStorage
        //when the window is closed
        window.onunload = _.bind(this.closeWindow, this);
    },
    getPageCount: function(pageStruct){
        for(var i=1; i<=parseInt(localStorage[this.pageCountName]); i++){
            if( pageStruct[i] === undefined ){
                return i;
            }
        }
        //If we make it here, no number is available
        //get the next sequential number
        return parseInt(localStorage[this.pageCountName]) + 1;
    },
    getWindowName: function(baseName){
        this.windowCount = this.addPageToLocalDB();
        return baseName + this.windowCount;
    },
    getTargetOrigin: function(){
        var protocol = window.location.protocol;
        var hostname = window.location.host;
        return protocol + '//' + hostname;
    },
    addPageToLocalDB: function(){
        var windowCount = 0;
        if(localStorage[this.localStorageKey] != undefined){

            //Determine the next number and set it in local storage
            var pageStruct = JSON.parse(localStorage[this.localStorageKey]);
            windowCount = this.getPageCount(pageStruct);
            pageStruct[windowCount] = true;
            localStorage[ this.localStorageKey ] = JSON.stringify(pageStruct);

            //Increment the total count
            localStorage[ this.pageCountName ] = parseInt(localStorage[ this.pageCountName ]) + 1;

        }else {
            //First page
            windowCount = 1;
            localStorage[ this.localStorageKey ] = JSON.stringify( { 1:true } );
            localStorage[ this.pageCountName ] = 1;
        }
        return windowCount;
    },
    closeWindow: function(){
        if(localStorage[this.localStorageKey] != undefined){
            var pageStruct = JSON.parse(localStorage[this.localStorageKey]);
            if(localStorage[ this.pageCountName ] > 1){
                //Remove page from page struct
                delete( pageStruct[this.windowCount] );
                //Decrement total count
                localStorage[ this.pageCountName ] = parseInt(localStorage[ this.pageCountName ]) - 1;
                //Store changes
                localStorage[ this.localStorageKey ] = JSON.stringify(pageStruct);
            }else{
                //last page delete out of local storage
                delete(localStorage[this.localStorageKey]);
                delete(localStorage[ this.pageCountName ]);
            }
        }
    },
    escapeForUrl: function(s){
        return encodeURIComponent( DV_PAGE.unescapeHtmlEntities(s) );
    },
    unescapeForUrl: function(s){
        return decodeURIComponent( DV_PAGE.unescapeHtmlEntities(s) );
    }

});

$(document).ready(function() {    

    DV_PAGE = new DataViewPage();

    console.log( DV_PAGE.urlObj );

    DV_PAGE.project = DV_PAGE.urlObj.data.attr.path.replace(/\//g, "");

    DV_PAGE.navLookup = jQuery.parseJSON( $('#dv_nav_json' ).attr('value') );
    DV_PAGE.refData = jQuery.parseJSON( $('#dv_reference_json' ).attr('value') );
    DV_PAGE.DataViewCollection = new DataViewCollection('#DataViewCollection', {});

    var dviewName = "";
    if( DV_PAGE.urlObj.data.attr.fragment != undefined ){
        dviewName = DV_PAGE.urlObj.data.attr.fragment.replace('#', '');
    }

    DV_PAGE.ConnectionsComponent = new ConnectionsComponent('#ConnectionsComponent', {});

    $(DV_PAGE.allViewsContainerSel).trigger(DV_PAGE.addDataViewEvent, { selected_dview:dviewName,
                                                                                              display_type:'pane' } );

});
