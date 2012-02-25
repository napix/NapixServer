define( [ 'libs/underscore/underscore' ], function( ) {
        var _ = window._;
        _.mixin({
                'objectify' : function( pairs) {
                    return _.reduce(
                        pairs,
                        function( memo, el) {
                            memo[ el[0] ] = el[1]
                            return memo
                        }, {} );
                }
            });
        return _
    });
