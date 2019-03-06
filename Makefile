dev-env:
	python -m virtualenv venv
	./venv/bin/python setup.py install

dist-api-docs:
	SPHINX_APIDOC_OPTIONS='members,private-members,undoc-members,show-inheritance' sphinx-apidoc -feTM -o shortfuse-docs/api .
	rm shortfuse-docs/api/shortfuse-docs* shortfuse-docs/api/setup.rst shortfuse-docs/api/test*

dist-docs:
	rm -rf shortfuse-docs/api/*.rst
	touch shortfuse-docs/api/.place_holder
	sphinx-build -T shortfuse-docs dist/docs

dist-publish:
	./venv/bin/python setup.py sdist upload -r rbs

