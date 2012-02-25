
define( [ 'napixclient', 'models/servers', 'models/credentials', 'test/jquery.mockjax' ],
    function( Client, Servers, Credentials, $) {
        Servers.reset( [ { 'host' : 'localhost' } ]);
        Credentials.reset( [
                { 'login' : 'lol', 'pass' : 'dude' },
                { 'login' : 'mpm', 'pass' : 'prefork' }
            ]);
        module('Client');
        test( 'Remaking', function() {
                equal( Client.napix, null);

                Credentials.at(0).select();
                equal( Client.napix, null);

                Servers.at(0).select();
                equal( Client.napix.server, 'localhost');
                equal( Client.napix.credentials.login, 'lol');
                equal( Client.napix.credentials.key, 'dude');
            });
        module( 'Client', {
                setup : function( ) {
                    Credentials.at(0).select();
                    Servers.at(0).select();
                    this.succes = $.mockjax({
                            url : 'http://localhost/success',
                            type : 'post',
                            responseText : { 'success': 'win' },
                        });
                    this.callCount = 0;
                    var modules = this;
                    this.level = $.mockjax({
                            url : 'http://localhost/p/_napix_help',
                            response : function() {
                                modules.callCount ++;
                                console.log( module, module.callCount);
                                this.responseText = { 'calls' : modules.callCount}
                            }
                        });
                    this.fail = $.mockjax({
                            url : 'http://localhost/fail',
                            'status' : 400,
                            responseText : { 'fail' : 'error' },
                            headers : {
                                'content-type' : 'application/json'
                            }
                        });
                },
                teardown : function() {
                    Client.unbind( 'error');
                    $.mockjaxClear( this.success);
                    $.mockjaxClear( this.level);
                    $.mockjaxClear( this.fail);
                }
            });
        asyncTest( 'Default Error handling', function() {
                Client.bind( 'error', function( code, text, object) {
                        equal(code, 400);
                        deepEqual( object, { 'fail' : 'error' });
                        start();
                    });
                Client.GET( '/fail', function() {
                        ok( false);
                        start();
                    });
            });
        asyncTest( 'Custom Error handling', 1, function() {
                Client.bind( 'error', function( code, text, object) {
                        ok( false);
                        start();
                    });
                Client.GET( '/fail',
                    function() {
                        ok( false);
                        start();
                    }, function() {
                        ok( true);
                        start();
                    });
            });
        asyncTest( 'Success', 1, function() {
                Client.POST( '/success', { 'complex' : 'data' }, function() {
                        ok( true);
                        start();
                    });
            });
        asyncTest( 'Cache resource', function() {
                var calls = 0;
                var cb = function( data ) {
                    equal( data.calls, 1);
                    ok(true);
                    calls ++;
                    if (calls == 2) {
                        equal( this.callCount, 1);
                        start();
                    }
                }.bind( this);
                Client.getLevel('/p', cb );
                Client.getLevel('/p', cb );
            });
    });
