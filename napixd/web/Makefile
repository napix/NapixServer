
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

