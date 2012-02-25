define( [ 'selecteditem', 'localstorage' ], function( si, Store) {
        var Model = si.Model.extend({
                defaults : {
                    'value' : 'void',
                    'selected' : false,
                }
            });
        var Collection = si.Collection.extend({
                model : Model,
                localStorage : new Store('__'),
            });

        module('Selected Item', {
                setup : function(){
                    this.collection = new Collection();
                    this.eleven = this.collection.create({ 'value' : 11 });
                    this.twelve = this.collection.create({ 'value' : 12 });
                    this.nineteen = this.collection.create({ 'value' : 19 });
                },
                teardown : function( ){
                    this.collection.reset();
                    localStorage.setItem('__', '')
                }
            });
        test( 'keep selected' , function() {
                this.nineteen.select();
                equal( this.collection.selected().get('value'), 19);
            });
        asyncTest( 'Send select', 1, function() {
                var collection = this.collection;
                this.collection.bind( 'select', function() {
                        ok( true, 'Event got fired' );
                        collection.unbind();
                        start();
                    });
                this.twelve.select();
            });
        asyncTest( 'Discard previous selected', 1, function() {
                this.nineteen.select();
                this.eleven.select();
                this.twelve.select();
                var collection = this.collection;
                setTimeout(function() {
                        ok( collection.reduce( function( memo, obj) {
                                    if ( obj.get('selected')) {
                                        return memo === null ? true : false;
                                    }
                                    return memo;
                                }, null));
                        start();
                    }, 100);
            });
    });
