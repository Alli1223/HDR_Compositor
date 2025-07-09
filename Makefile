.PHONY: run gui package-linux package-windows

run:
	docker build -f Dockerfile.web -t hdr-webapp .
	# run container and stop it cleanly on Ctrl+C
	docker run --rm -p 3000:3000 --name hdr-webapp-container hdr-webapp & \
	pid=$$!; trap "docker stop hdr-webapp-container >/dev/null" INT TERM; \
	wait $$pid

# Launch the desktop HDR compositor GUI
gui:
        python hdr_gui.py

# Build a standalone binary for Linux using PyInstaller
package-linux:
        pyinstaller --onefile hdr_gui.py --name hdr_compositor

# Display Windows packaging instructions
package-windows:
        @echo "Run 'pyinstaller --onefile hdr_gui.py --name hdr_compositor' on a Windows machine"


