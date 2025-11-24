CFLAGS += -std=c99
CFLAGS += -O3
CFLAGS += -Wall -Werror -Wextra

%.so: %.o
	$(CC) -shared -fPIC -o $@ $<


default: _decimate.so

clean:
	rm -f *.so *.o *.pyc
