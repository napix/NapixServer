define( ['json/viewer', 'jQuery'] , function( JSONView, $) {
        module( 'json viewer');
        test( 'Boolean False', function() {
                var el = $(JSONView.getView( false ).render().el);
                equal( el.text(), 'false');
            });
        test( 'Boolean True', function() {
                var el = $(JSONView.getView( true ).render().el);
                equal( el.text(), 'true');
            });
        test( 'Null', function() {
                var el = $(JSONView.getView( null ).render().el);
                equal( el.text(), 'null');
            });
        test( 'Empty Array', function() {
                var el = $(JSONView.getView( [] ).render().el);
                equal( el.text(), 'Empty Array');
            });
        test( 'Empty Object', function() {
                var el = $(JSONView.getView( {} ).render().el);
                equal( el.text(), 'Empty Object');
            });
        test( 'Empty String', function() {
                var el = $(JSONView.getView( '' ).render().el);
                equal( el.text(), 'Empty String');
            });
        test( 'String', function() {
                var el = $(JSONView.getView( 'Honi Soit Qui Mal Y Pense' ).render().el);
                equal( el.text(), 'Honi Soit Qui Mal Y Pense');
            });
        test( 'Array', function() {
                var el = JSONView.getView( ['a','b'] ).render().el;
                equal( el.tagName, 'OL');
                equal( $(el).children('li').length, 2);
                equal( $(el).text(), 'ab');
            });
        test( 'Object', function() {
                var el = JSONView.getView( { 'a' : 'mpm','b' : null } ).render().el;
                equal( el.tagName, 'UL');
                equal( $(el).children('li').length, 2);
                equal( $(el).text(), 'a mpmb null');
            });
    });
