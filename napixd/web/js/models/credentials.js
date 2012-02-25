
define([
        'selecteditem',
        'localstorage',
    ], function( Selected, Store) {
        var Credential = Selected.Model.extend({
                defaults : {
                    'login' : 'login',
                    'pass' : 'secret',
                    'selected' : false,
                },
                validate : function() {
                    if ( !( this.get('login') && this.get('pass'))) {
                        return 'You need to define a login and a pass';
                    }
                }
            });
        var CredentialsList = Selected.Collection.extend({
                model : Credential,
                localStorage : new Store('credentials')
            });
        return new CredentialsList();
    });
