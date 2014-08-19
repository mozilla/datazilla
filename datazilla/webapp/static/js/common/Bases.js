/******* 
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this file,
 * You can obtain one at http://mozilla.org/MPL/2.0/. 
 * *****/
String.prototype.hashCode = function(){
    //Builds a 32bit integer hash of a string
    var hash = 0, i, charCode;
    if (this.length == 0) return hash;
    for (i = 0; i < this.length; i++) {
        charCode = this.charCodeAt(i);
        hash = ((hash<<5)-hash)+charCode;
        hash = hash & hash; // Convert to 32bit integer
    }
    return Math.abs(hash);
};
var Page = new Class({

    Implements:Options,

    jQuery:'Page',

    initialize: function(selector, options){
        this.urlObj = jQuery.url(window.location);

        //Hardcoding here for speed, we need to encode/decode
        //lots of anchor values
        this.encodeHtmlEntities = [  [ new RegExp('&', 'g'), '&amp;' ],
                                              [ new RegExp('<', 'g'), '&lt;' ],
                                              [ new RegExp('>', 'g'), '&gt;' ],
                                              [ new RegExp('"', 'g'), '&quot;' ] ];

        this.decodeHtmlEntities = [  [ new RegExp('&amp;', 'g'), '&' ],
                                              [ new RegExp('&lt;', 'g'), '<' ],
                                              [ new RegExp('&gt;', 'g'), '>' ],
                                              [ new RegExp('&quot;', 'g'), '"' ] ];

    },
    registerSubscribers: function(subscriptionTargets, el, context){
        if(el === undefined){
            console.log( 'registerSubscribers error: el is undefined' );
        }
        for(var ev in subscriptionTargets){
            if(subscriptionTargets.hasOwnProperty(ev)){
                $( el ).bind(ev, {}, _.bind(function(event, data){
                    if( _.isFunction( subscriptionTargets[ event.type ] ) ){
                        data['event'] = event;
                        _.bind( subscriptionTargets[ event.type ], context, data)();
                    }else {
                        console.log( 'registerSubscribers error: No function for ' + event.type );
                    }
                }, context));
            }
        }
    },
    unbindSubscribers: function(subscriptionTargets, el){
        for(var ev in subscriptionTargets){
            if(subscriptionTargets.hasOwnProperty(ev)){
                $(el).unbind( ev, subscriptionTargets[ev] );
            }
        }
    },
    escapeHtmlEntities: function(str){
        for (var i=0; i<this.encodeHtmlEntities.length; i++){
            str = str.replace(this.encodeHtmlEntities[i][0], this.encodeHtmlEntities[i][1]);
        }
        return str;
    },
    unescapeHtmlEntities: function(str){
        if(str != undefined){
            for (var i=0; i<this.decodeHtmlEntities.length; i++){
                str = str.replace(this.decodeHtmlEntities[i][0], this.decodeHtmlEntities[i][1]);
            }
        }
        return str;
    }
});
var Component = new Class({

    Implements:Options,

    jQuery:'Component',

    initialize: function(selector, options){
    }
});
var Model = new Class({

    Implements:Options,

    jQuery:'Model',

    initialize: function(selector, options){
    }
});
var View = new Class({

    Implements:Options,

    jQuery:'View',

    initialize: function(selector, options){

        this.requestErrorSel = '#hp_failed_get_dialogue';
        this.requestStatusSel = '#hp_text_status';
        this.requestCodeSel = '#hp_status_code';
        this.requestErrorThrownSel = '#hp_error_thrown';

    },
    getId: function(id, dviewIndex){
        return id.replace(/\#/, '') + '_' + dviewIndex;
    },
    getIdSelector: function(id, dviewIndex){
        var newId = "";
        if(id.search(/^\#/) > -1){
            newId = id + '_' + dviewIndex;
        }else{
            newId = '#' + id + '_' + dviewIndex;
        }
        return newId;
    },
    getAlphabeticalSortKeys: function(sortTarget){

        var key = "";
        var keys = [];
        for (key in sortTarget){
            if (sortTarget.hasOwnProperty(key)){
               keys.push(key);
            }
        }
        return keys.sort();
    },
    convertTimestampToDate: function(unixTimestamp, getHMS){

        var dateObj = new Date(unixTimestamp * 1000);

        var year = dateObj.getFullYear();
        var month = this.padNumber(dateObj.getMonth() + 1, 10, '0');
        var day = this.padNumber(dateObj.getDate(), 10, '0');

        var dateString = year + '-' + month + '-' + day;

        if(getHMS){

            var hours = this.padNumber(dateObj.getHours(), 10, '0');
            var minutes = this.padNumber(dateObj.getMinutes(), 10, '0');
            var seconds = this.padNumber(dateObj.getSeconds(), 10, '0');

            dateString += ' ' + hours + ':' + minutes + ':' + seconds;
        }

        return dateString;
    },
    convertUTCTimestampToDate: function(utcTimestamp, getHMS){

        var dateObj = new Date(utcTimestamp * 1000);

        var year = dateObj.getUTCFullYear();
        var month = this.padNumber(dateObj.getUTCMonth() + 1, 10, '0');
        var day = this.padNumber(dateObj.getUTCDate(), 10, '0');

        var dateString = year + '-' + month + '-' + day;

        if(getHMS){

            var hours = this.padNumber(dateObj.getUTCHours(), 10, '0');
            var minutes = this.padNumber(dateObj.getUTCMinutes(), 10, '0');
            var seconds = this.padNumber(dateObj.getUTCSeconds(), 10, '0');

            dateString += ' ' + hours + ':' + minutes + ':' + seconds;
        }

        return dateString;

    },
    padNumber: function(n, max, pad){

        n = parseInt(n);

        if( n < max ){
            return pad + n;
        }

        return n;
    },
    hexToRgb: function(hex) {

        var result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);

        //Add alpha channel to lighten the color
        var rgbAlpha = 'rgba(' + parseInt(result[1], 16) + ',' +
            parseInt(result[2], 16) + ',' +
            parseInt(result[3], 16) + ',0.1)';

        return rgbAlpha;
    },
    requestError: function(jqXHR, textStatus, errorThrown){

        $(this.requestStatusSel).text(textStatus);
        $(this.requestCodeSel).text(errorThrown.status);
        $(this.requestErrorThrownSel).text(errorThrown.statusText);

        $(this.requestErrorSel).dialog();
    }
});
