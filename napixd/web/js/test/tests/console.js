define( ['console', 'models/history', 'jQuery' , 'models/consoleentries'] ,
    function( ConsoleView, History, $, ConsoleEntries){
        module( 'PromptView', {
                'setup' : function( ){
                    History.reset([
                            { 'command' : 'one' },
                            { 'command' : 'two' },
                            { 'command' : 'three' },
                            { 'command' : 'four' }
                        ]);
                    this.console = new ConsoleView();
                },
                teardown : function( ) {
                    ConsoleEntries.unbind( 'add');
                }
            });
        test( 'history navigation', function() {
                var prompt_ = this.console.prompt_;
                var el = $(prompt_.render().el)

                equal( el.prop('value'), '');

                el.prop('value', 'zero');
                prompt_.historyDown();
                equal( el.prop('value'), 'zero');
                prompt_.historyUp();
                equal( el.prop('value'), 'one');
                prompt_.historyUp();
                equal( el.prop('value'), 'two');
                prompt_.historyUp();
                prompt_.historyUp();
                equal( el.prop('value'), 'four');
                prompt_.historyUp();
                equal( el.prop('value'), 'four');

                prompt_.historyDown();
                equal( el.prop('value'), 'three');
                prompt_.historyDown();
                prompt_.historyDown();
                equal( el.prop('value'), 'one');
                prompt_.historyDown();
                equal( el.prop('value'), 'zero');
            })
        asyncTest( 'help', 2, function() {
                ConsoleEntries.bind( 'add', function( x) {
                        ok(
                            x.get('level') == 'query' && x.get('text') == 'help' ||
                            x.get('level') == 'json'
                        );
                        if( x.get('level') == 'json') start();
                })
                this.console.compute( 'help');
            });
        asyncTest( 'help help', 2, function() {
                ConsoleEntries.bind( 'add', function( x) {
                        ok(
                            x.get('level') == 'query' && x.get('text') == 'help help' ||
                            x.get('level') == 'help'
                        );
                        if( x.get('level') == 'help') start();
                })
                this.console.compute( 'help help');
            });
    });
