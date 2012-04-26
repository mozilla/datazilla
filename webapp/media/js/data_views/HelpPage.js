/******* 
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this file,
 * You can obtain one at http://mozilla.org/MPL/2.0/. 
 * *****/
var HPAGE;

var HelpPage = new Class( {

   jQuery:'HelpPage',

   initialize: function(selector, options){

      this.waitMessageSel = '#dv_help_spinner';
      this.helpContentSel = '#dv_help_content';
   }

});

$(document).ready(function() {   

   HPAGE = new HelpPage();

   //Toggle off wait message and display help contents
   $(HPAGE.waitMessageSel).addClass('hidden');
   $(HPAGE.helpContentSel).removeClass('hidden');
   
});
