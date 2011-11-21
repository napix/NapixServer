#!/bin/bash
dir=`dirname $0`
find "$dir/" -name 'test_*.py' | xargs -n1 python
