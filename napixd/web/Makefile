
.PHONY: js clean test

all: js


js:
	r.js -o client/js/app.build.js

clean:
	rm -r client/build/

test:
	mocha -u tdd -R spec client/test



