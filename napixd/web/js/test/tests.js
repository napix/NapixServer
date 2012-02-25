QUnit.config.autostart = false;
require.config({
        baseUrl : '../'
    });

define([ 'config' ], function() {
        require([
                'test/tests/napixclient',
                'test/tests/selecteditem',
                'test/tests/history',
                'test/tests/jsonviewer',
                'test/tests/napix',
                'test/tests/jsoneditor',
                'test/tests/console'
            ], function () {
                QUnit.start();
            })
    });
