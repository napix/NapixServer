
define( [ 'Backbone', 'localstorage' ], function( Backbone, Store ) {
        var ConsoleEntry = Backbone.Model.extend({
                defaults : {
                    'text' : '',
                    'level' : 'info',
                },
            });
        var ConsoleEntriesList = Backbone.Collection.extend({
                model : ConsoleEntry,
                localStorage : new Store('console'),
            });
        return new ConsoleEntriesList();
    });
