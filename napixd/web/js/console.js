//depends : JSONView ConsoleEntries History consoleActions jQuery Backbone underscore
//depends-js : jsonviewer.js models.js consoleactions.js jquery.js backbone.js underscore.js
//***************************** Console ************************

  define( [
          'Backbone',
          'underscore',
          'jQuery',
          'json/viewer',
          'models/history',
          'models/consoleentries',
          'consoleactions'
      ],function( Backbone, _, $, JSONView, History, ConsoleEntries, consoleActions ) {
          var ConsoleEntryTextView = Backbone.View.extend({
                  tagName : 'div',
                  className : 'console-entry-text',
                  render :  function() {
                      this.$el
                      .text( this.model.get('text') );
                      return this;
                  }
              });
          var ConsoleEntryPreView = ConsoleEntryTextView.extend({
                  tagName : 'pre'
              });
          var ConsoleEntryQueryView = Backbone.View.extend({
                  className : 'console-entry-query',
                  render : function() {
                      this.$el
                      .append( $('<span />', { 'text' : '>>>' } ))
                      .append( this.model.get('text') );
                      return this;
                  }
              });
          var ConsoleEntryJSONView = Backbone.View.extend({
                  render : function() {
                      var data  = this.model.get('text');
                      this.$el
                      .append( new JSONView(data).render().el);
                      return this;
                  }
              });
          var ConsoleEntryView = Backbone.View.extend({
                  initialize : function(model ) {
                      this.inside = ConsoleEntryView.getView( model)
                      this.setElement( this.inside.el);
                  },
                  render : function( ) {
                      this.inside.render();
                      this.$el.addClass( 'console-entry');
                      return this;
                  }
              },{
                  getView : function(model) {
                      if ( model.get('level') in this.viewsMap) {
                          return new this.viewsMap[ model.get('level') ]({ model : model });
                      }
                      return new this.defaultView({ model : model });
                  },
                  viewsMap : {
                      'query' : ConsoleEntryQueryView,
                      'help' : ConsoleEntryPreView,
                      'json' : ConsoleEntryJSONView
                  },
                  defaultView : ConsoleEntryTextView
              });
          var PromptView = Backbone.View.extend({
                  initialize :  function() {
                      this.setElement( $('#console-input'));
                      this.focus();

                      this.keymap = this.getKeyMap();
                      this.$el.keypress( this.onKeyPress.bind(this) );
                      $('#console-go').click( this.validate.bind(this) );

                      this._historyPosition = -1;
                      this._historyStore = '';
                  },
                  getKeyMap : function() { return {
                          13: this.validate,
                          38: this.historyUp,
                          40: this.historyDown,
                      }},
                  onKeyPress : function(ev) {
                      var action = this.keymap[ev.keyCode];
                      if (action) action.call(this);
                  },
                  historyUp :  function() {
                      if ( ! History.hasMore(this._historyPosition)) {
                          return ;
                      }
                      if ( this._historyPosition == -1) {
                          this._historyStore = this.$el.attr('value');
                      }
                      this._historyPosition ++ ;
                      this.$el.attr('value',
                          History.at(this._historyPosition).get('command'));
                  },
                  historyDown :  function() {
                      if ( this._historyPosition == -1) {
                          return ;
                      }
                      this._historyPosition -- ;
                      if ( this._historyPosition == -1) {
                          this.$el.attr('value', this._historyStore);
                      } else {
                          this.$el.attr('value',
                              History.at(this._historyPosition).get('command'));
                      }
                  },
                  validate : function() {
                      this._historyPosition = -1;

                      var text =  this.$el.attr('value');
                      History.push(text);
                      this.trigger( 'input', text);
                      this.$el.attr('value', '');
                      this.focus();
                  },
                  focus : function() {
                      this.$el.focus();
                  }
              });
          var ConsoleView = Backbone.View.extend({
                  initialize : function() {
                      this.setElement( $('#console-body'));
                      ConsoleEntries.bind( 'add', this.addOne, this);
                      ConsoleEntries.reset();
                      this._initActions();

                      $('#console-clean').click( this.clear.bind(this) );
                      this.prompt_ = new PromptView();
                      this.prompt_.bind ('input', this.compute, this);
                  },
                  _initActions : function() {
                      this.actions = _.extend({
                              'clear' : this.clear,
                              'help' : this.help,
                          },
                          consoleActions);
                      this.actions.clear.help = 'Clear the screen';
                      this.actions.help.help = [
                          'Usage : help [command]',
                          'help',
                          '   Show the list of functions',
                          'help command',
                          '   Show the help of the given command'].join('\n')
                  },
                  compute : function( input) {
                      ConsoleEntries.create( { 'level': 'query', 'text': input });
                      tokens = input.split(' ')
                      if ( ! _.any( tokens) ) {
                          return;
                      }
                      if (tokens[0] in this.actions) {
                          result = this.actions[tokens.shift()].apply(this, tokens);
                          if (result) {
                              ConsoleEntries.create( { 'level' :'response',
                                      'text': result })
                          }
                      } else {
                          ConsoleEntries.create( { 'level': 'notfound',
                                  'text': 'No such method "'+tokens[0]+'"' });
                      }
                  },
                  gotJSON : function( path, data) {
                      ConsoleEntries.create( { 'level': 'json', 'text' : data });
                  },
                  addOne : function(consoleEntry) {
                      var view = new ConsoleEntryView( consoleEntry);
                      this.$el.append(view.render().el);
                      this.$el.scrollTop(this.$el.height());
                  },
                  clear : function() {
                      this.$el.empty();
                      this.show();
                  },
                  help : function( command) {
                      if ( command && command in this.actions) {
                          ConsoleEntries.create({ 'level': 'help', 'text' : this.actions[command].help });
                      } else {
                          ConsoleEntries.create({ 'level': 'json', 'text' : _.keys( this.actions) })
                      }
                  },
                  show : function() {
                      this.prompt_.focus()
                  }
              });
          return ConsoleView;
      });
