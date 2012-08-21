
.PHONY: js clean test quality

all: js


js:
	r.js -o client/js/app.build.js

clean:
	rm -r client/build/

test:
	NODE_PATH=/usr/lib/node_modules/ mocha -u tdd -R spec client/test

quality:
	find client/js -name '*.js' -and -not -path 'client/js/libs/*'\
 	   	-and -not -name 'app.build.js' |\
		xargs jshint --config client/.jshintrc --show-non-errors

coverage:
	test -d client/js-cov && rm -r client/js-cov || true
	jscoverage 'client/js' 'client/js-cov' --no-instrument='libs'
	NODE_PATH=/usr/lib/node_modules/ NAPIX_WEBCLIENT_COVERAGE=yes mocha -u tdd -R html-cov client/test > client/cov.html
