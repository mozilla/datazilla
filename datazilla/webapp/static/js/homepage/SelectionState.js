/*******
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this file,
 * You can obtain one at http://mozilla.org/MPL/2.0/.
 * *****/
var SelectionState = new Class({

    jQuery:'SelectionState',

    initialize: function(selector, options){

        this.stateKeys = {
                'selected':false,
                'product':'',
                'repository':'',
                'os':'',
                'os_version':'',
                'arch':'',
                'test':'',
                'page':''
            };

        this.defaultProject = 'talos';

        this.projectDefaults = {
            'b2g':{
                'product':'B2G',
                'repository':'master',
                'arch':'Gonk',
                'test':'phone',
                'page':''
                },
            'talos':{
                'product':'Firefox',
                'repository':'Mozilla-Inbound',
                'arch':'x86_64',
                'test':'tp5o',
                'page':'',
                },
            'default':{
                'product':'Firefox',
                'repository':'Mozilla-Inbound',
                'arch':'x86_64',
                'test':'tp5o',
                'page':''
                }
            };

        this.selections = {};
    },
    getSelectedProjectData: function(){

        var selectedProject = {};
        var project = "";
        for(project in this.selections){
            if(this.selections.hasOwnProperty(project)){
                if(this.selections[project]['selected'] === true){
                    selectedProject = this.selections[project];
                    selectedProject['project'] = project;
                }
            }
        }

        return selectedProject;
    },
    getProjectData: function(project){
        return this.selections[project];
    },
    setUrlObj: function(urlObj){

        var project = urlObj.param.query.project || this.defaultProject;

        this.setDefaults(project);

        this.setProject(project);
        this.setArchitecture(urlObj.param.query.arch);
        this.setProduct(urlObj.param.query.product);
        this.setRepository(urlObj.param.query.repository);
        this.setTest(urlObj.param.query.test_name);
        this.setPage(urlObj.param.query.page);

    },
    setDefaults: function(project){

        if(this.selections[project] === undefined){

            this.selections[project] = jQuery.extend(true, {}, this.stateKeys);

            var defaults = {};
            if(this.projectDefaults[project] === undefined){
                defaults = this.projectDefaults['default'];
            }else{
                defaults = this.projectDefaults[project];
            }

            var projectKey = "";

            for(projectKey in defaults){
                this.selections[project][projectKey] = defaults[projectKey];
            }
        }
    },
    setProject: function(project){

        if(project === undefined){
            return;
        }

        this.setDefaults(project);
        this.selections[project]['selected'] = true;

        //Unselect any previously selected projects
        var p = "";
        for(p in this.selections){
            if(this.selections.hasOwnProperty(p)){
                if(p != project){
                    this.selections[p]['selected'] = false;
                }
            }
        }
    },
    setProduct: function(project, product){

        if(!_.isString(project)){
            return;
        }
        this.setDefaults(project);
        this.selections[project]['product'] = product;
    },
    setRepository: function(project, repository){

        if(!_.isString(repository)){
            return;
        }
        this.setDefaults(project);
        this.selections[project]['repository'] = repository;
    },
    setOs: function(project, os){

        if(!_.isString(os)){
            return;
        }
        this.setDefaults(project);
        this.selections[project]['os'] = os;
    },
    setOsVersion: function(project, osVersion){

        if(!_.isString(osVersion)){
            return;
        }
        this.setDefaults(project);
        this.selections[project]['os_version'] = osVersion;
    },
    setArchitecture: function(project, architecture){
        if(!_.isString(architecture)){
            return;
        }
        this.setDefaults(project);
        this.selections[project]['arch'] = architecture;
    },
    setTest: function(project, test){
        if(!_.isString(test)){
            return;
        }
        this.setDefaults(project);
        this.selections[project]['test'] = test;
    },
    setPage: function(project, page){
        if(!_.isString(page)){
            return;
        }
        this.setDefaults(project);
        this.selections[project]['page'] = page;
    }
});
