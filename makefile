# vim: set noet:
EXECS=bin/rain-run bin/rain-dis bin/rain-step
LIB=lib/librain.so

LIB_OBJS=build/core.o build/vm.o build/instr.o build/table.o build/builtins.o
EXEC_OBJS=build/run.o build/dis.o build/step.o

LDFLAGS=-Llib
CFLAGS=-Iinclude
LIBS=$(LIB) -lgc -ldl

all: build lib env $(LIB) $(EXECS)

build:
	mkdir -p build

lib:
	mkdir -p lib

$(LIB): $(LIB_OBJS)
	clang $(LDFLAGS) -fPIC -shared -o $@ $^

$(LIB_OBJS): build/%.o: rvm/%.c
	clang $(CFLAGS) -fPIC -c -o $@ $^

$(EXEC_OBJS): build/%.o: rvm/%.c
	clang $(CFLAGS) -c -o $@ $^

$(EXECS): bin/rain-%: build/%.o $(LIB)
	clang $(LDFLAGS) $(LIBS) -o $@ $<

clean:
	rm -f $(EXECS) $(LIB) $(LIB_OBJS) $(EXEC_OBJS)

env:
	python3 -m venv env
	env/bin/pip install --upgrade pip wheel
	env/bin/pip install -r requirements.txt
	env/bin/pip install -e .
	for x in $(EXECS); do ln -s $$(pwd)/$$x env/$$x; done

test:
	@env/bin/py.test -v

lint:
	@env/bin/flake8 rain --max-line-length=100 --ignore=E11,E114,E121,E221
