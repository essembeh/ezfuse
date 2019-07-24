.PHONY: install watch build publish clean tests coverage flake8

all: clean flake8

venv: requirements.txt
	virtualenv -p python3 venv --no-site-packages
	./venv/bin/pip install -r requirements.txt
	touch venv

clean:
	rm -rf flake-report 

flake8:
	flake8 src/

install:
	test -n "$(VIRTUAL_ENV)"
	python3 setup.py install
	#python3 setup.py install_data

watch:
	test -n "$(VIRTUAL_ENV)"
	rerun  -d src -p "*.py" -x "make install >/dev/null 2>&1"

build: tests
	rm -rf dist/
	python3 setup.py sdist bdist_wheel

publish: build
	twine upload --repository-url https://upload.pypi.org/legacy/ dist/*
