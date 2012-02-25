//depends : Client jQuery Backbone JSONView underscore
//depends-js : napixclient.js jsonviewer.js jquery.js backbone.js underscore.js
//***************************** Napix path view *************************

  define( [
          'Backbone',
          'jQuery',
          'underscore',
          'napixclient',
          'json/viewer',
          'json/editor'
      ],
      function(Backbone, $, _, Client, JSONView, JSONEditView ) {
          var PathView = Backbone.View.extend({
                  tagName : 'div',
                  initialize : function( path, parentMetaData) {
                      this.path = path;
                      this.parentMetaData = parentMetaData;

                      //parentMetaData = parentMetaData || null;
                      if (_.isNull(parentMetaData) ) {
                          //first level
                          Client.getLevel( this.path, this.gotMetaData.bind(this) );

                      } else if ( _.isString(parentMetaData)) {
                          //heritier d'une connection indirecte
                          Client.getLevel( parentMetaData + '/' + (this.path.split('/').pop()),
                              this.gotMetaData.bind(this) );

                      } else if ( parentMetaData['direct_plug']  == true ) {
                          // connection directe
                          Client.getGenericLevel( this.path, this.gotMetaData.bind(this) );

                      } else if ( parentMetaData['direct_plug'] == false) {
                          //connections séparée par des mots clés
                          _.defer( this.gotMetaData.bind(this, parentMetaData['absolute_url']) );
                      }
                      // else parentMetaData.direct_plug == null
                      // pas d'heritiers
                  },
                  render :  function() {
                      $('<div />', { 'class' : 'explorer-header'})
                      .append($('<i />', { 'class' : 'deploy' }))
                      .append($('<span />', { 'text' : this.path, 'class': 'path'})
                          .click( this.selectObject.bind( this) ))
                      .appendTo( this.el);

                      return this;
                  },
                  getList : function( ) {
                      Client.GET( this.path + '/' , this.gotList.bind(this) );
                  },
                  gotList : function( pathList ) {
                      var el = this.$('.explorer-content').first().empty();
                      this.$('.deploy').first().addClass( 'icon-minus');
                      this.contentViews = _( pathList)
                      .chain()
                      .filter( function(path ) {
                              return path.search('/_napix') == -1
                          })
                      .map( function( path) {
                              var view = new PathView( path, this.metaData);
                              view.bind( 'select', this.refire, this );
                              el.append( view.render().el );
                              return view;
                          }, this)
                      .map( function( view) {
                              return [view.path, view ];
                          })
                      .objectify()
                      .value();
                      this.trigger( 'gotList', this.contentViews);
                      this.unbind( 'gotList');
                  },
                  gotMetaData : function( metaData) {
                      this.metaData = metaData || null;
                      $('<div />', { 'class' : 'explorer-content' })
                      .appendTo(this.el);
                      this.$('.deploy')
                      .first()
                      .addClass('icon-plus')
                      .click( this.toggleContent.bind(this) );
                      this.trigger( 'gotMetaData');
                      this.unbind( 'gotMetaData');
                  },
                  getObject : function() {
                      if ( ! _.isString(this.parentMetaData) ) {
                          Client.GET( this.path , this.gotObject.bind(this) );
                      } else {
                          this.gotObject();
                      }
                  },
                  gotObject : function( object) {
                      if (object) {
                          this.object = object;
                      }
                      this.trigger('select', this);
                  },
                  selectObject : function() {
                      if ( _.isUndefined( this.object) ) {
                          this.object = null;
                          this.getObject();
                      } else {
                          this.gotObject();
                      }
                  },
                  toggleContent : function( force ) {
                      if ( !this.filled ) {
                          this.filled = true;
                          this.getList();
                      } else if ( _.isBoolean( force)) {
                          this.$('.explorer-content').first().toggle( force );
                          this.$('.deploy').first().addClass( force ? 'icon-plus' :'icon-minus');
                      } else {
                          var shown = this.$('.explorer-content').first().toggle().css('display') == 'none';
                          this.$('.deploy').first().addClass( shown ? 'icon-plus' :'icon-minus');
                      }
                  },
                  refire : function( view) {
                      this.trigger('select', view);
                  },
                  setSelected : function( selected) {
                      this.$('.explorer-header').first().toggleClass('selected', selected);
                  },
                  refreshObject : function() {
                      delete this.object;
                      this.selectObject();
                  },
                  refreshContent : function() {
                      this.filled = false;
                      this.toggleContent();
                  },
                  goToPath : function( path) {
                      if ( this.path == path ) {
                          this.selectObject();
                      } else if ( path.search( this.path) == 0) {
                          if ( this.metaData) {
                              this.toggleContent( true );
                          } else {
                              this.bind( 'gotMetaData', this.toggleContent.bind(this) );
                          }
                          var goToContent = function( views ) {
                              _.any( views, function(view, key) {
                                      if (path.search( key) == 0) {
                                          view.goToPath( path);
                                          return true;
                                      }
                                      return false;
                                  });
                          }
                          if ( this.contentViews ) {
                              goToContent( this.contentViews );
                          } else {
                              this.bind( 'gotList',  goToContent );
                          }
                      }
                  }
              });
          var RootView = Backbone.View.extend({
                  initialize : function() {
                      this.deployed = false;
                  },
                  render :  function() {
                      this.$el
                      .append(
                          $('<div />', { 'text' : '/' })
                          .one( 'click', this.deploy.bind(this)))
                      .append(
                          $('<div />', { 'class' : 'explorer-content' } )) ;
                      return this;
                  },
                  goToPath : function( path) {
                      this.deploy();
                      var goToContent = function( views) {
                          console.log( views);
                          _.any( views, function(view, key) {
                                  if (path.search( key) == 0) {
                                      view.goToPath( path);
                                      return true;
                                  }
                                  return false;
                              });
                      }
                      if ( this.views) {
                          goToContent( this.views);
                      } else {
                          this.bind( 'gotList', goToContent);
                      }
                  },
                  deploy : function() {
                      if ( ! this.deployed) {
                          Client.GET('/', this.gotList.bind(this) );
                          this.deployed = true;
                      }
                  },
                  gotList : function( pathList ) {
                      var el = this.$('.explorer-content');
                      this.views = _( pathList)
                      .chain()
                      .map(function( path) {
                              var view = new PathView( path, null);
                              view.bind( 'select', this.refire, this );
                              el.append( view.render().el );
                              return view;
                          }, this)
                      .map( function( view ){
                              return [ view.path, view];
                          })
                      .objectify()
                      .value();
                      this.trigger( 'gotList', this.views);
                      this.unbind( 'gotList');
                  },
                  refire : function( view) {
                      this.trigger('select', view);
                  }
              });

          //***************************** Explorer *************************
          var ExplorerObjectEmptyView = Backbone.View.extend({
                  tagName : 'em',
                  render : function() {
                      this.$el.text('empty');
                      return this;
                  }
              });
          var ExplorerObjectBaseView = Backbone.View.extend({
                  id : '',
                  emptyView : ExplorerObjectEmptyView,
                  initialize : function() {
                      this.setElement( $('#'+ this.id));
                      this.shown = false;
                      this.rendered = false;
                      this.view = new this.emptyView();
                      $('#'+this.id+'-label')
                      .bind( 'shown' , this.show.bind( this))
                      .bind( 'hidden' , this.hide.bind( this));
                  },
                  gotObject : function( object) {
                      this.rendered = false;
                      this.view = object ? new this.insideView( object ) : new this.emptyView();
                      return this.render();
                  },
                  render : function() {
                      if ( !this.rendered && this.shown) {
                          this.rendered = true;
                          this.actuallyRender();
                      }
                      return this;
                  },
                  actuallyRender : function() {
                      this.$el
                      .empty()
                      .append( this.view.render().el );
                      this.trigger('rendered', this.view);
                  },
                  available : function( avail) {
                      $('#'+this.id+'-label').toggle( Boolean(avail ));
                      if (!avail) {
                          this.shown = false;
                      }
                  },
                  hide : function() {
                      this.shown = false;
                      return this;
                  },
                  show : function() {
                      this.shown = true;
                      this.render();
                      return this;
                  }
              });
          var ExplorerObjectView = ExplorerObjectBaseView.extend({
                  id : 'explorer-object',
                  insideView : JSONView,
                  gotObject : function( object, metaData ) {
                      this.path = metaData.path
                      this.actions = metaData.actions;
                      this.deletable = metaData.deletable;
                      this.editable = metaData.editable;

                      ExplorerObjectView.__super__.gotObject.call( this, object);
                      return this;
                  },
                  actuallyRender : function() {
                      ExplorerObjectView.__super__.actuallyRender.call( this);
                      //console.log( this.actions)
                      var el = $('<div />',  { 'id': 'explorer-object-actions', 'class': 'btn-group' })
                      .appendTo( this.el);

                      if ( this.actions ) {
                          _.each( this.actions, function( action) {
                                  $('<button />', { 'text': action, 'class' : 'btn' })
                                  .click( _.bind( this.trigger, this, 'action', action, this.path ))
                                  .appendTo( el);
                              }, this);
                      }
                      if ( this.deletable ) {
                          $('<button />', { 'text': 'Delete', 'class': 'btn btn-danger' })
                          .click( _.bind( this.trigger, this, 'delete', this.path))
                          .appendTo( el);
                      }
                      if ( this.editable ) {
                          $('<button />', { 'text': 'Edit', 'class' : 'btn' })
                          .click( _.bind( this.trigger, this, 'edit', this.path ))
                          .appendTo( el);
                      }
                      return this;
                  }
              });
          var ExplorerHelpView = ExplorerObjectBaseView.extend({
                  id: 'explorer-help',
                  insideView : JSONView,
              });
          var ExplorerEditorBaseView = ExplorerObjectBaseView.extend({
                  insideView : JSONEditView,
                  initialize :function() {
                      ExplorerEditorBaseView.__super__.initialize.call( this);
                      this.bind( 'rendered', this.onRender, this );
                  },
                  gotObject : function( object, metaData ) {
                      this.path = metaData.path;
                      ExplorerEditorBaseView.__super__.gotObject.call( this, object);
                  },
                  onRender : function( view) {
                      view.bind('validate', _.bind( this.trigger, this, 'validate', this.path));
                  },
              });
          var ExplorerEditView = ExplorerEditorBaseView.extend({
                  id: 'explorer-edit'
              });

          var JSONCreateView = Backbone.View.extend({
                  initialize : function( collectionPath) {
                      this.collectionPath = collectionPath;
                  },
                  render : function() {
                      Client.getNewObject( this.collectionPath, this.gotTemplate.bind(this) );
                      return this;
                  },
                  gotTemplate : function( template) {
                      //console.log( 'template', template)
                      var view = new JSONEditView( template);
                      $( this.el).append( view.render().el);
                      view.bind('validate', _.bind( this.trigger, this, 'validate'))
                  }
              });
          var ExplorerCreateView = ExplorerEditorBaseView.extend({
                  id: 'explorer-create',
                  insideView : JSONCreateView,
              });
          var ActionCallView = Backbone.View.extend({
                  initialize : function( path, action) {
                      this.setElement( $( '#explorer-action-call-body'));
                      this.path = path;
                      this.action = action;
                      this.actionUrl = this.path + '/_napix_action/' + this.action
                      this.optionnalView = null;
                      this.mandatoryView = null;
                  },
                  render : function() {
                      Client.GET( this.actionUrl + '/_napix_help',
                          this.gotActionMetaData.bind( this) );
                      this.$el
                      .empty()
                      .append( $('<h3 >', { text : this.path +' - '+ this.action }));
                      return this;
                  },
                  gotActionMetaData : function( metaData ) {
                      var mandatory = _.reduce( metaData.mandatory, function(acc, value) {
                              acc[ value ] = '';
                              return acc;
                          }, {} );
                      this.$el.addClass('json-edit');
                      if ( ! _.isEmpty( mandatory) ) {
                          this.mandatoryView = new JSONEditView.defaultView( mandatory).disableAddKey();
                          this.$el
                          .append( $('<h4 />', { 'text' : 'Mandatory parameters' }))
                          .append( this.mandatoryView.render().el);
                      }
                      if ( ! _.isEmpty( metaData.optional)) {
                          this.optionnalView = new JSONEditView.defaultView( metaData.optional).disableAddKey();
                          this.$el
                          .append( $('<h4 />', { 'text' : 'Optionnal parameters' }))
                          .append( this.optionnalView.render().el);
                      }
                      this.$el.append(
                          $('<div />')
                          .append( $( '<input />', { 'value' : 'Valider' , 'class' : 'validate-button'  }))
                          .click( this.validate.bind(this) )
                      );
                      $('#explorer-action-call').show();
                      this.$('input').first().focus();
                  },
                  validate : function() {
                      Client.POST( this.actionUrl , this.getValue(), this.gotResult.bind( this) );
                  },
                  gotResult : function( result ) {
                      this.$el
                      .empty()
                      .append( new JSONView( result).render().el );
                  },
                  getValue : function() {
                      return _.extend(
                          this.mandatoryView && this.mandatoryView.getValue() || {},
                          this.optionnalView && this.optionnalView.getValue() || {}
                      );
                  }
              });
          var ExplorerView = Backbone.View.extend({
                  initialize : function() {
                      this.setElement( $('#explorer'));
                      this.object = new ExplorerObjectView();
                      this.help = new ExplorerHelpView();
                      this.edit = new ExplorerEditView();
                      this.create = new ExplorerCreateView();
                      Client.bind( 'error', this.gotError, this );

                      this.edit.bind( 'validate', this.sendPUT, this );
                      this.edit.available( false);

                      this.create.bind( 'validate', this.sendPOST, this );
                      this.object
                      .bind( 'edit' , this.showEdit , this)
                      .bind( 'delete', this.sendDELETE, this)
                      .bind( 'action', this.callAction, this)
                      .show();

                      $('#explorer-tabs a[data-toggle="tab"]').bind( 'show', this.changeTab.bind( this));
                      Client.bind('change', this.selectServer, this);

                      this.currentView = null;
                      this.rootView = null;
                  },
                  changeTab : function( ev ) {
                      $( ev.relatedTarget).trigger( 'hidden' );
                  },
                  showEdit : function() {
                      $('#explorer-edit-label').tab('show');
                  },
                  goToPath : function( path) {
                      if ( this.rootView) {
                          this.rootView.goToPath( path);
                      } else {
                          this.bind( 'selectServer', function() {
                                  this.rootView.goToPath( path);
                              }.bind( this) );
                      }
                  },
                  gotError : function( code, text, content){
                      $('<div />', { 'class' : 'alert alert-block alert-error' })
                      .append( $('<a />', { 'class' : 'close' , 'data-dismiss' : 'alert', 'text': 'X'}))
                      .append( $('<h4 />', {'class' : 'error-msg', 'text' :code + ' '+ text } ))
                      .append(
                          _.isString( content ) && $( '<span />', { 'text': content }) ||
                          !_.isEmpty( content) && content.jquery && content ||
                          new JSONView( content).render().el)
                      .prependTo( this.el);
                  },
                  selectServer : function( napix) {
                      $('#server').text(
                          napix.credentials.login + '@' + napix.server
                      );
                      this.rootView = new RootView();
                      //location.hash.split(':')[1] || '/'

                      this.rootView.bind('select', this.select, this);
                      $('#explorer-server').empty().append( this.rootView.render().el );

                      // Load something
                      //this._gotSomething('#explorer-object',
                      //{"resource_fields": {"file": {"example": "/etc/hosts", "description": "Path of the hosts file"}}, "direct_plug": true, "absolute_url": "/hosts/*", "doc": "\n    Host Files manager\n    ", "managed_class": ["HostManager"], "collection_methods": ["HEAD", "GET"], "actions": [], "resource_methods": ["HEAD", "GET"]});
                      this.trigger( 'selectServer');
                      this.unbind( 'selectServer');
                  },
                  select : function( view ) {
                      if ( this.currentView != null) {
                          this.currentView.setSelected(false);
                      }
                      //location.hash = '#object:'+view.path;

                      view.setSelected(true);
                      this.create.available( view.metaData && _.contains( view.metaData.collection_methods , 'POST'));

                      this.object.gotObject( view.object, {
                              'path' : view.path,
                              'actions' : view.parentMetaData && view.parentMetaData.actions || [] ,
                              'editable' : Boolean(view.parentMetaData && _.contains( view.parentMetaData.resource_methods, 'PUT' )),
                              'deletable' : Boolean( view.parentMetaData && _.contains( view.parentMetaData.resource_methods, 'DELETE' )),
                          });
                      this.edit.gotObject( view.object, {
                              'path' : view.path
                          });
                      this.help.gotObject( view.metaData && ! _.isString(view.metaData) ? view.metaData : view.parentMetaData  );
                      this.create.gotObject( view.path, {
                              'path' : view.path
                          });

                      $('#explorer-object-label').tab('show');

                      this.currentView = view;
                      this.trigger( 'selected', view.path);
                  },
                  sendPUT : function( path, object) {
                      Client.PUT( path, object,
                          this.currentView.refreshObject.bind( this.currentView ) );
                  },
                  sendPOST : function( path, object ) {
                      console.log( 'path', path)
                      console.log( 'object', object);
                      Client.POST( path + '/', object,  function() {
                              this.currentView.refreshContent() ;
                          }.bind(this) );
                  },
                  sendDELETE : function( path ) {
                      Client.DELETE( path,
                          _.bind( this.goToPath, this, path.split('/').slice(0,-1).join('/') ));
                  },
                  callAction : function( action, path) {
                      var view = new ActionCallView( path, action).render();
                  }
              });
          return ExplorerView;
      });
