//depends : Backbone ExplorerView ConsoleView jQuery SelectorsView
//depends-js : backbone.js explorer.js console.js jquery.js selectors.js

define([
        'jQuery',
        'Backbone',
        'explorer',
        'console',
        'selectors',
        'bootstrap'
], function( $, Backbone, ExplorerView, ConsoleView, SelectorsView) {
        var PanelsView = Backbone.View.extend({
                el : 'body',
                initialize : function() {
                    this.explorer = new ExplorerView();
                    this.console = new ConsoleView();
                    this.selectors = new SelectorsView();
                    $('#explorer-label a').tab('show');
                    $('#console-label a').bind('shown',
                        this.console.show.bind( this.console));
                }
            });
        //************************* Application ****************************

          var AppRouter = Backbone.Router.extend({
                  initialize : function( ) {
                      this.panels = new PanelsView();
                      this.panels.explorer.bind( 'selected', this.navigate, this)
                  },
                  routes : {
                      'console' : 'showConsole',
                      '*path/' : 'goToPath',
                      '*path' : 'goToPath',
                      '/' : 'showConsole',
                  },
                  goToPath : function( path) {
                      this.panels.explorer.goToPath( path[0] != '/' && '/' + path || path);
                  }
              });
          return AppRouter;
      });
