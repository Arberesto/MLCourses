all: pyenv-activate create-venv deps

run:
	. venv/bin/activate; PYTHONPATH=src; python src/main.py --vk_token '0f1954bb7d4da7de0a529636f5a080e946fb2ec4a80692ed40231dd99f531e778bfa8a607dd1b9626b644' --vk_group_id 191130961;

deps:
	./venv/bin/activate; pip install --upgrade pip;
	./venv/bin/activate; pip install --upgrade setuptools;
	./venv/bin/activate; pip install -r requirements.txt;

create-venv: pyenv-activate;
	python -m venv venv

pyenv-activate:
	pyenv local; # it get info from .python-version file
.PHONY: deps create-venv pyenv pyenv-activate source
