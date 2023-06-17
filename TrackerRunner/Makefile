PHASE_TIME=180

run0:
	docker compose -f docker-compose-async-runner.yml up runner-0

run1:
	@sleep $$(($(PHASE_TIME) * 1))
	docker compose -f docker-compose-async-runner.yml up runner-1

run2:
	@sleep $$(($(PHASE_TIME) * 2))
	docker compose -f docker-compose-async-runner.yml up runner-2

run3:
	@sleep $$(($(PHASE_TIME) * 3))
	docker compose -f docker-compose-async-runner.yml up runner-3

run4:
	@sleep $$(($(PHASE_TIME) * 4))
	docker compose -f docker-compose-async-runner.yml up runner-4


async-distributor: run0 run1 run2 run3 run4
	

run-async:
	make -j 5 async-distributor