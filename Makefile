%.so: %.o
	$(CC) -shared -fPIC -o $@ $<

%.o: %.c
	$(CC) -O3 -std=c99 -c -o $@  $<

default: _decimate.so

clean:
	rm -f *.so *.o *.pyc
