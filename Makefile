CFLAGS += -std=c99
CFLAGS += -O3
CFLAGS += -Wall -Werror -Wextra

%.so: %.o
	$(CC) -shared -fPIC -o $@ $<


default: _decimate.so lightweight-venv

clean:
	rm -f *.so *.o *.pyc
	rm -rf lightweight-venv .venv __pycache__

lightweight-venv: Pipfile.lock
	dls-py3 pipfilelock-to-venv
	touch lightweight-venv

Pipfile.lock: Pipfile
	PIPENV_VENV_IN_PROJECT=1 pipenv lock
