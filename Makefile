all: executable index.cgi

index.cgi:
	ln -s pyle.cgi index.cgi

executable:
	chmod a+x pyle.cgi
	chmod a+x sublanguages/sequence-helper.sh

clean:
	rm -f $$(find . -name '*.pyc')
	rm -f pyledb_cache/*
