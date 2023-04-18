lint:
	-pipenv run black --check .
	-pipenv run flake8
	-pipenv run yamllint .
	-pipenv run pylint --disable all --enable spelling --recursive=y ./

lint-fix:
	-pipenv run black .
	-pipenv run flake8
	-pipenv run yamllint .
	-pipenv run pylint --disable all --enable spelling --recursive=y ./