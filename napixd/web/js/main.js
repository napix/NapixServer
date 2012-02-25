define([ 'config' ], function() {
        require([
                'Backbone',
                'jQuery',
                'napix-ui'
            ], function( Backbone, $, AppRouter )  {
                $(document).ready(function() {
                        var app = new AppRouter();
                        Backbone.history.start();
                    });
            });
    });
