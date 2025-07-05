.PHONY: run

run:
	docker build -f Dockerfile.web -t hdr-webapp .
	docker run --rm -p 3000:3000 hdr-webapp

# Run the HDR GUI application
#run:
#	python hdr_gui.py

