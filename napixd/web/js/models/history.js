define( [ 'Backbone', 'localstorage' ], function( Backbone, Store) {
        var HistoryCommand = Backbone.Model.extend({
                defaults : {
                    command : ''
                }
            });
        var HistoryList = Backbone.Collection.extend({
                model : HistoryCommand,
                localStorage : new Store('history'),
                hasMore : function( index) {
                    return this.length >= index + 2;
                },
                push : function( command) {
                    this.create({ 'command' : command }, { at : 0 });
                },
            });
        return new HistoryList();
    })

