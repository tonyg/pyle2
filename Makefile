all:

clean:
	rm -f $$(find . -name '*.pyc')
	rm -f pyledb_cache/*
