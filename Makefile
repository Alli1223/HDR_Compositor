.PHONY: run

run:
	docker build -f Dockerfile.web -t hdr-webapp .
	docker run --rm -p 3000:3000 hdr-webapp
