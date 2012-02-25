
define( ['json/editor', 'jQuery', 'bootstrap'] , function( JSONEditView, $) {
        module('json edit view');
        test( 'Edit View', function() {
                var v = new JSONEditView({ 'a' : 1, 'b' : [ 1, 2, false] }).render();
                deepEqual( v.getValue(), { 'a' : 1, 'b' : [ 1, 2, false] });
                v.showText();
                deepEqual( v.getValue(), { 'a' : 1, 'b' : [ 1, 2, false] });
            });
    });

