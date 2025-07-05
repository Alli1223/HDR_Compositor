.PHONY: run

run:
	# Use BuildKit directly so buildx is not required
	DOCKER_BUILDKIT=1 docker build -f Dockerfile.web -t hdr-webapp .
	# run container and stop it cleanly on Ctrl+C
	docker run --rm -p 3000:3000 --name hdr-webapp-container hdr-webapp & \
	pid=$$!; trap "docker stop hdr-webapp-container >/dev/null" INT TERM; \
	wait $$pid

# Run the HDR GUI application
#run:
#	python hdr_gui.py

