//depends NapixClient Credentials Server underscore jsSHA
//depends-js : models.js napix.js underscore.js sha256.js
//***************************** Client *************************


  define([
          'Backbone',
          'underscore',
          'napix',
          'models/servers',
          'models/credentials'
      ], function( Backbone, _, NapixClient, Servers, Credentials ) {
          var CachableResource = function( suffix) {
              this.suffix = suffix,
              this._resources = {};
          };
          CachableResource.prototype = {
              getResource : function( path, callback ) {
                  if ( this._resources[path] && _.isArray( this._resources[path]) ) {
                      this._resources[path].push(callback);
                  } else if ( this._resources[ path ] ) {
                      _.defer( callback, this._resources[path]);
                  } else {
                      this._resources[path] = [ callback ];
                      Client.GET( path + this.suffix , _.bind( this.gotResource, this, path ) );
                  }
              },
              gotResource : function( path, resource) {
                  _.each( this._resources[path] , function(cb) {
                          cb( resource);
                      });
                  this._resources[path] = resource;
              },
              renew : function() {
                  this._resources = {}
              }
          };

          var Client = {
              napix: null,
              _levels : new CachableResource( '/_napix_help'),
              _newObjects : new CachableResource( '/_napix_new'),
              make : function() {
                  this._levels.renew();
                  this._newObjects.renew();
                  if ( Servers.selected() && Credentials.selected()) {
                      this.napix = new NapixClient(
                          Servers.selected().get('host'),
                          Credentials.selected().get('login'),
                          Credentials.selected().get('pass')
                      );
                      this.trigger('change', this.napix);
                  }
              },
              GET : function( path, callback, onError) {
                  this.request( 'GET' , path, null, callback, onError);
              },
              HEAD : function( path, callback, onError) {
                  this.request( 'HEAD' , path, null, callback, onError);
              },
              PUT : function( path, object, callback, onError) {
                  this.request( 'PUT' , path, object, callback, onError);
              },
              POST : function( path, object, callback, onError) {
                  this.request( 'POST' , path, object, callback, onError);
              },
              DELETE : function( path, callback, onError) {
                  this.request( 'DELETE' , path, null, callback, onError);
              },
              request : function( method, path, object, callback, onError) {
                  //* XXX ADD LAG FOR DEBUG */ setTimeout(function() {
                  this.napix.request( method , path, object, callback, onError || this.onError.bind( this));
                  //* XXX ADD LAG FOR DEBUG */ }.bind(this), 500)
              },
              onError : function( result) {
                  console.log( result)
                  this.trigger( 'error',
                      result['status'],
                      result['statusText'],
                      result.getResponseHeader('content-type') == 'application/json' && JSON.parse(result.responseText) ||
                      result.getResponseHeader('content-type') == 'text/html' && $(result.responseText) ||
                      result.responseText
                  );
              },
              getLevel : function( path, callback) {
                  return this._levels.getResource( path, callback);
              },
              getNewObject : function( path, callback) {
                  return this._newObjects.getResource( path, callback);
              },
              getGenericLevel : function( path, callback) {
                  var splitPath = path.split('/')
                  splitPath.pop();
                  splitPath.push('*');
                  return this.getLevel( splitPath.join('/'), callback);
              },
          };
          _.extend(Client, Backbone.Events);
          Servers.bind( 'select', Client.make, Client );
          Credentials.bind( 'select', Client.make, Client );

        return Client;
      });
