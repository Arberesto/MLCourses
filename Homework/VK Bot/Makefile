all: pyenv-activate create-venv deps

run:
	. venv/bin/activate; PYTHONPATH=src; python src/main.py;

deps:
	./venv/bin/activate; pip install --upgrade pip;
	./venv/bin/activate; pip install --upgrade setuptools;
	./venv/bin/activate; pip install -r requirements.txt;

create-venv: pyenv-activate;
	python -m venv venv

pyenv-activate:
	pyenv local; # it get info from .python-version file
.PHONY: deps create-venv pyenv pyenv-activate source
