//depends : Credentials Servers underscore
//depends-js : models.js underscore.js

define( [
        'underscore',
        'napixclient',
        'models/credentials',
        'models/servers',
    ], function( _, Client, Credentials, Servers) {
        var consoleActions = {};
        var Action  = function( collection, filter, usage, callbacks ) {
            var action = new ActionDecorator( collection, filter, usage, callbacks );
            return action.call.bind(action);
        }

        var ActionDecorator = function( collection, filter, usage, callbacks ) {
            this.filter  =filter;
            this.collection = collection;
            this.usage = usage;
            this.callbacks = callbacks;
        };

        ActionDecorator.prototype = {
            call : function() {
                result = this.callback.apply( this, arguments);
                if (!result) {
                    return this.usage;
                }
            },
            searchModel : function( id) {
                return (
                    this.collection.find( function(model) {
                            return model.get( this.filter ) == id  },
                        this) ||
                    this.collection.find( function(model) {
                            return model.get( this.filter ).search( id ) != -1 },
                        this)
                );
            },
            callback : function( option, id ) {
                if ( ! option && !id) {
                    return false;
                }
                var action = id && option || 'choose';

                var remaining = _.rest(arguments, 2);
                if ( action == 'add' && id ) {
                    remaining.unshift(id) ;
                    return (this.callbacks['add'] || this.defaults['add'] ).apply(this, remaining );
                }

                var model = this.searchModel( id || option) ;
                remaining.unshift(model);
                if ( action == 'choose' && model) {
                    return ( this.callbacks['choose'] || this.defaults['choose'] ).apply( this, remaining );
                } else if (action == 'del' && model) {
                    return ( this.callbacks['del'] || this.defaults['del'] ).apply( this, remaining );
                }
            },
            defaults : {
                'choose' : function( object) {
                    object.select();
                    return true;
                },
                'add' : function( id) {
                    var obj = {};
                    obj[this.filter] = id;
                    this.collection.create( obj ).select();
                    return true;
                },
                'del' : function( object) {
                    object.destroy();
                    return true;
                }
            }
        }

        consoleActions.login  = Action(
            Credentials, 'login', 'Usage: login [add|del|choose] username [password]', {
                'choose' : function( cred, pass) {
                    if ( pass && cred.get('pass') != pass) {
                        cred.set({'pass': pass});
                        cred.save();
                    }
                    cred.select();
                    return true;
                },
                'add' : function(login, pass) {
                    console.log( login, pass)
                    if ( pass ) {
                        Credentials.create( { 'login' : login, 'pass' : pass }).select();
                        return true;
                    }
                    return false;
                }
            });
        consoleActions.login.help = [
            'Usage: login [add|del|choose] login [pass]',
            'login username',
            'login choose login',
            '  Select the credentials which match login',
            'login choose username pass',
            '  Update te credentials matching username',
            'login add username pass',
            '  add the given credentials',
            'login del username',
            '  remove the credentials matching username'
        ].join('\n')

        consoleActions.server = Action(
            Servers, 'host', 'Usage: server [add|del|choose] hostname', { });
        consoleActions.server.help = [
            'Usage: server [add|del|choose] hostname',
            'server hostname',
            'server choose hostname',
            '  Select the server which match hostname',
            'server add hostname',
            '  add the server at the host <hostname>',
            'server del hostname',
            '  remove the server matching hostname'
        ].join('\n')


        consoleActions.GET = function( url) {
            if( ! url) {
                return 'Usage: GET url'
            }
            Client.GET( url, _.bind(this.gotJSON, this, url) );
        }
        consoleActions.GET.help = ' Send a GET request a the given url'

        return consoleActions;
    });
