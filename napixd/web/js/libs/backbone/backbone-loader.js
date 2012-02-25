define([ 'order!libs/underscore/underscore',
        'order!libs/backbone/backbone',
        'jQuery' ], function( a,b,$ ) {
        Backbone.setDomLibrary( $ );
        return Backbone.noConflict() ;
    });
