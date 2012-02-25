define( [ 'libs/jquery/jquery' ], function( ){
        var $ = jQuery.noConflict();
        $.fn.orDefault = function(defaultVal) {
            return this.length && this || $(defaultVal);
        };
        return $;
    });
