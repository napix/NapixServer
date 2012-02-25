
define( ['napix', 'underscore', 'test/jquery.mockjax' ],
    function( NapixClient, _,$) {
        module( 'Napix Client', {
                setup : function() {
                    this.client = new NapixClient( 'localhost', 'dude', 'secret');
                    this.oldDate = Date.now;
                    Date.now = function() { return 123000000 };
                    this.mockjaxId = $.mockjax({
                            url : 'http://localhost/p/',
                            responseText : {
                                'ok' : true,
                                'mpm': 'prefork'
                            }
                        });
                },
                teardown : function() {
                    Date.now = this.oldDate;
                    $.mockjaxClear( this.mockjaxId);
                }
        });
        test( 'nonce randomness', function() {
                var nonces = _.times(50, this.client.getNonce);
                ok( _.all( nonces, function(x, i, all){
                        return _.lastIndexOf(all, x) == i;
                    }));
            });
        test( 'authorization', function() {
                this.client.getNonce = function( ) {  return 'abcd-efgh' };
                equal( this.client._getAuthorization( 'GET' , '/'),
                    'login=dude&nonce=abcd-efgh&host=localhost&path=/&method=GET&timestamp=123000:ec868bfd29e3937738968b6a03096f2de0e0da43ee7b263302a59d6deef3c3c0'
                );
            });
        asyncTest( 'request', 1, function() {
                this.client.request( 'GET', '/p/', null,
                    function( data ) {
                        deepEqual( data, {
                            'ok' : true,
                            'mpm': 'prefork'
                        });
                        start();
                    },
                    function( data) {
                        ok( false);
                        start();
                    });
            });
    });
