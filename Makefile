CFLAGS += -std=c99
CFLAGS += -O3
CFLAGS += -Wall -Werror -Wextra

%.so: %.o
	$(CC) -shared -fPIC -o $@ $<


default: _decimate.so build-venv

clean:
	rm -f *.so *.o *.pyc
	rm -rf .venv __pycache__

build-venv: Pipfile.lock
	PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy --ignore-pipfile
	

Pipfile.lock: Pipfile
	PIPENV_VENV_IN_PROJECT=1 pipenv lock --pre --python dls-python3
