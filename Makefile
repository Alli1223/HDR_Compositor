.PHONY: run

run:
	docker build -f Dockerfile.web -t aeb-webapp .
	# run container and stop it cleanly on Ctrl+C
	docker run --rm -p 3000:3000 --name aeb-webapp-container aeb-webapp & \
	pid=$$!; trap "docker stop aeb-webapp-container >/dev/null" INT TERM; \
	wait $$pid

# Run the AEB compositor GUI
#run:
#	python aeb_gui.py

