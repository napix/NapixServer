define( [ 'models/history', 'underscore' ], function( History, _) {
        module( 'history', {
                setup : function() {
                    History.reset([
                            { 'command' : '1' },
                            { 'command' : '2' },
                            { 'command' : '3' },
                            { 'command' : '4' },
                        ]);
                },
                teardown : function() {
                    History.reset();
                }
        });
        test( 'push', function() {
                History.push( '0');
                ok(
                    _.reduce(
                        _.zip([ '0', '1', '2', '3', '4' ], History.pluck('command')),
                        function( memo, x ) {
                            return memo && x[0] == x[1];
                        }, true));
            });
        test( 'Has More', function() {
                ok( History.hasMore( 0) , '0')
                ok( History.hasMore( 2), ' length -1')
                ok( ! History.hasMore( 3), ' length')
            });
    });

