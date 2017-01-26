#!/bin/sh
# fixes the commandlineargs.out
echo 1 > tests/outputs/commandlineargs.out
echo $(pwd)/commandlineargs >> tests/outputs/commandlineargs.out
echo "\$RAIN_TEST = testing" >> tests/outputs/commandlineargs.out
