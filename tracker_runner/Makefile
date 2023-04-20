lint:
	-poetry run black --check .
	-poetry run flake8
	-poetry run yamllint .
	-poetry run pylint --disable all --enable spelling --recursive=y ./

lint-fix:
	-poetry run black .
	-poetry run flake8
	-poetry run yamllint .
	-poetry run pylint --disable all --enable spelling --recursive=y ./

rabbitmq:
	docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3.11-management