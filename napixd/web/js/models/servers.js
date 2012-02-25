
define([
        'selecteditem',
        'localstorage'
    ], function(Selected, Store) {
        var Server = Selected.Model.extend({
                defaults : {
                    'host' : 'localhost',
                    'selected' : false
                },
                validate : function() {
                    if ( ! this.get('host')) {
                        return 'You need to define an host';
                    }
                }
            });
        var ServersList = Selected.Collection.extend({
                model : Server,
                localStorage : new Store('servers')
            });
        return new ServersList();
    });
