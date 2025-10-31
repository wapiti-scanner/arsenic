# Makefile for the arsenic project

PACKAGE_NAME := wapiti-arsenic
IMAGE_NAME_DEB := debian:testing
IMAGE_NAME_RPM := fedora:41

.PHONY: all test release format lint docs clean clean-all deb rpm

# Default target when running `make`
all: format lint test

# Run tests with coverage report
test:
	@echo "--- Running tests with coverage ---"
	poetry run pytest --cov=src/$(PACKAGE_NAME) --cov-report=term-missing

# Create sdist and wheel distributions
release:
	@echo "--- Building release artifacts ---"
	poetry build

# Build Debian package (.deb) using Docker
deb: release
	@echo "--- Building Debian package in Docker (${IMAGE_NAME_DEB}) ---"
	@mkdir -p build/deb
	# Copy sdist to the build dir (needed by the container)
	cp dist/*.tar.gz build/deb/

	# Run the build inside a Debian container
	docker run --rm \
		-v $(PWD):/app \
		-w /app/build/deb \
		${IMAGE_NAME_DEB} /bin/bash -c "set -e; \
			apt update && apt install -y build-essential debhelper python3 python3-setuptools python3-poetry-core python3-dev dh-python pybuild-plugin-pyproject fakeroot python3-pip python3-venv; \
			python3 -m venv /tmp/venv; \
			source /tmp/venv/bin/activate; \
			/tmp/venv/bin/pip install poetry build; \
			export PATH=/tmp/venv/bin:$$PATH; \
			/tmp/venv/bin/poetry install --no-root; \
			tar -xzf *.tar.gz --strip 1; \
			cp -r /app/packaging/debian ./debian; \
			rm -f ./debian/compat; \
			dpkg-buildpackage -us -uc -b; \
		"
	@echo "--- Debian package generated successfully ---"

# Build RPM package (.rpm) using Docker
rpm: release
	@echo "--- Building RPM package in Docker (fedora:40) ---"
	rm -rf build/rpm
	mkdir -p build/rpm/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
	# Copy both tarball and wheel
	cp dist/*.tar.gz build/rpm/SOURCES/wapiti-arsenic-28.4.tar.gz
	cp dist/*.whl build/rpm/SOURCES/
	cp packaging/wapiti-arsenic.spec build/rpm/SPECS/
	docker run --rm \
		-v $(PWD):/app \
		-w /app \
		${IMAGE_NAME_RPM} /bin/bash -c "set -e; \
		dnf update -y && \
		dnf install -y rpm-build python3-devel python3-pip && \
		rpmbuild --define '_topdir /app/build/rpm' -ba /app/build/rpm/SPECS/wapiti-arsenic.spec"
	@echo "--- RPM package generated in build/rpm/RPMS/ ---"

# Publish release to PyPI using twine
publish: release
	@echo "--- Publishing package to PyPI ---"
	poetry run twine upload dist/*

# Format code using black
format:
	@echo "--- Formatting code ---"
	poetry run black src tests docs

# Lint code using pylint
lint:
	@echo "--- Linting code ---"
	poetry run pylint src tests

# Generate documentation
docs:
	@echo "--- Generating documentation ---"
	$(MAKE) -C docs html

# Clean up generated files
clean:
	@echo "--- Cleaning up project ---"
	rm -rf dist
	rm -rf .pytest_cache
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	$(MAKE) -C docs clean

# Clean everything, including packaging artifacts
clean-all: clean
	@echo "--- Cleaning all packaging artifacts ---"
	rm -rf build
	rm -rf *.egg-info