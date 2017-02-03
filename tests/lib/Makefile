ifndef CLANG
	CLANG=clang
endif

.PHONY: all
all: init suite test

.PHONY: init
init: criterion criterion/build/libcriterion.so

criterion:
	git clone https://github.com/Snaipe/Criterion criterion --branch v2.3.0-1 --depth 1

criterion/build/libcriterion.so:
	cd criterion && mkdir build && cd build && cmake .. && cmake --build .

suite: init
	$(CLANG) -I criterion/include -Lcriterion/build -lcriterion -lgc -lpcre suite.c ../../lib/*.c ../../lib/*/*.c -o suite

.PHONY: test
test: suite
	LD_LIBRARY_PATH=./criterion/build ./suite
