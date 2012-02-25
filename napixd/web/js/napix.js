//depends : jQuery underscore
//depends-js : jquery.js underscore.js
define( [
        'jQuery',
        'underscore',
        'jsSHA'
    ], function($, _, jsSHA)  {

        NapixClient = function( server, login, key ) {
            this.server = server;
            this.credentials = {
                login : login,
                key: key
            };
            return this;
        };

        _.extend(NapixClient.prototype, {
                sign : function(msg, key) {
                    var shaobj = new jsSHA( msg, 'ASCII');
                    return shaobj.getHMAC(key , 'ASCII', 'SHA-256', 'HEX' );
                },
                _getAuthorization : function(method, uri) {
                    var request = {
                        login : this.credentials.login,
                        nonce : this.getNonce(),
                        host : this.server,
                        path : uri,
                        method : method,
                        timestamp : String(Math.floor(Date.now()/1000))
                    };
                    var body = this._encodeParams(request);
                    var signature = this.sign( body, this.credentials.key)
                    return body + ':' + signature ;
                },
                _encodeParams : function( params) {
                    tail = [];
                    for (var p in params) {
                        tail.push(p + "=" + escape(params[p]));
                    }
                    return tail.join('&');
                },
                getNonce : function() {
                    return _.map(
                        _.range(8),
                        function() {
                            return (((1+Math.random())*0x10000)|0).toString(16);
                        }).join('');
                },
                request : function(method, uri, data, callback, onError) {
                    /*
                    console.log({
                            //crossDomain : true,
                            url : 'http://' + this.server + uri,
                            type : method,
                            data : data && JSON.stringify(data),
                            //accepts : 'application/json',
                            dataType : 'json',
                            contentType : 'application/json',
                            success  : callback,
                            error : onError || this.onError,
                            //complete : console.log,
                            headers : {
                                'Authorization' : this._getAuthorization( method, uri)
                            }
                        })*/
                    $.ajax({
                            //crossDomain : true,
                            url : 'http://' + this.server + uri,
                            type : method,
                            data : data && JSON.stringify(data),
                            //accepts : 'application/json',
                            dataType : 'json',
                            contentType : 'application/json',
                            success  : callback,
                            error : onError || this.onError,
                            //complete : console.log,
                            headers : {
                                'Authorization' : this._getAuthorization( method, uri)
                            }
                        });
                }
            });
        return NapixClient;
    });

