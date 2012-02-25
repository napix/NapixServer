
define( [ 'Backbone' ,'underscore' ], function( Backbone, _) {
        var SelectedItem = Backbone.Model.extend({
                select : function() {
                    if ( ! this.get('selected')) {
                        this.set( {'selected': true } );
                        this.collection.select( this) ;
                        this.save();
                    }
                    return this;
                }
            });
        var SelectedList = Backbone.Collection.extend({
                initialize : function() {
                    this.bind( 'reset', this.sendSelect, this);
                    this._selected = null;
                },
                select : function(x) {
                    this._selected = x;
                    _.each(this.without(x),
                        function(y) {
                            y = y.set({'selected': false});
                            if(y) y.save()
                            });
                    this.trigger( 'select', x );
                },
                sendSelect : function() {
                    var item = this.find( function(x) { return x.get('selected')}) ;
                    if (item ) {
                        this.select( item);
                    }
                },
                selected : function() {
                    return this._selected;
                }
            });
        return {
            'Model' : SelectedItem,
            'Collection' : SelectedList
        }
    });
