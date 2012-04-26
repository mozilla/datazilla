/******* 
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this file,
 * You can obtain one at http://mozilla.org/MPL/2.0/. 
 * *****/
var ConnectionsComponent = new Class({

   Extends: Component,

   jQuery:'ConnectionsComponent',

   initialize: function(selector, options){

      this.setOptions(options);

      this.parent(options);

      this.view = new ConnectionsView('#ConnectionsView',{});
      this.model = new ConnectionsModel('#ConnectionsModel',{});

   },
   open: function(tab, signals){
      this.setAllViewsOptionMenu(this.view.viewListSel, signals);
      this.view.open(tab);
   },
   getDisplayType: function(){
      return this.view.displayType;
   },
   setAllViewsOptionMenu: function(selectSel, signals){
      var dviewNames = DV_PAGE.DataViewCollection.getDataViewsBySignalHash(signals);
      //Set up all views option menu
      this.view.setAllViewsOptionMenu(selectSel, dviewNames);
   },
   setDataViewIndex: function(index){
      this.view.dviewIndex = index;
   }

});
var ConnectionsView = new Class({

   Extends:View,

   jQuery:'ConnectionsView',

   initialize: function(selector, options){

      this.setOptions(options);

      this.parent(options);

      //List of hashes containing:
      // name:dviewName, read_name:readName
      this.dviewNames = this.options.dviewNames;

      this.allViewsContainerSel = '#dv_view_container';

      //Main modal container selector
      this.connectionsModalClassSel = '.dv-connections-modal';

      //Tab Selectors 
      this.openNewViewTabSel = '#dv_open_new_view_tab';

      //Select menu selectors
      this.viewListSel = '#dv_view_list';

      //Radio buttons
      this.radioButtonOpenClassSel = '.dv-page-newpane';

      //Events
      this.addDataViewEvent = 'ADD_DATAVIEW';

      //Index of the view that opened the dialog, set at runtime
      this.dviewIndex = undefined;

      this.initializeModal();
   },

   initializeModal: function(){

      //Set up the tag selection events
      this.setTabSelections();

      $(this.connectionsModalClassSel).dialog({ 
         autoOpen: false,
         width:400,
         height:600,
         buttons:this.getDialogButtons(),
         modal:true
      });
   },
   getDialogButtons: function(){

      var buttons = {
            "Cancel": function(){
               $(this).dialog('close');
            },
            "Open":_.bind(function(event){

               //Get the dview the user selected
               var selectedView = this.getDataViewSelection();
               //Close the dialog
               $(this.connectionsModalClassSel).dialog('close');

               var displayType = $('input[name=open]:checked').val();

               //Trigger the add view event
               $(this.allViewsContainerSel).trigger(this.addDataViewEvent, { selected_dview:selectedView, 
                                                                           parent_dview_index:this.dviewIndex,
                                                                           display_type:displayType });

            }, this)
         };

      return buttons;
   },
   getDataViewSelection: function(){
      return $(this.viewListSel).attr('value');
   },
   setAllViewsOptionMenu: function(listSel, dviewNames){

      //Clear out any existing options
      $(listSel).empty();

      dviewNames.sort(this.sortOptionMenu);

      for(var i=0; i<dviewNames.length; i++){
         var optionEl = $('<option></option>');
         $(optionEl).attr('value', dviewNames[i].name);
         $(optionEl).text(dviewNames[i].read_name);
         if( i === 0 ){
            $(optionEl).attr('selected', 1);
         }
         $(optionEl).css('display', 'block');
         $(listSel).append(optionEl);
      }
   },
   sortOptionMenu: function(a, b){
      if( a.read_name.search(/^Site/) && b.read_name.search(/^Unit/) ){
         return 1;   
      }else{
         return -1;
      }
   },
   setTabSelections: function(){
      $(this.connectionsModalClassSel).tabs({
         select: function(event, ui){
            this.tabSelection = $(this.openNewViewTabSel).attr('href');
         }
      });
   },
   open: function(tab){

      var tabSel;
      if(tab === 'open'){
         tabSel = this.openNewViewTabSel;
      }

      $(this.connectionsModalClassSel).tabs("select", tabSel);

      $(this.connectionsModalClassSel).dialog('open');
   }
});
var ConnectionsModel = new Class({

   Extends:View,

   jQuery:'ConnectionsModel',

   initialize: function(options){

      this.setOptions(options);

      this.parent(options);

   }
});
