PYTHON_VER ?= 3.12

run: deps
	venv/bin/streamlit run streamlit-concurrency.py --logger.level=INFO # --server.address=0.0.0.0

test-watch:
	source venv/bin/activate && venv/bin/ptw src

test: deps
	venv/bin/pytest src

format: deps
	venv/bin/ruff format .
deps: venv/.deps_installed

venv/.deps_installed: venv requirements.txt
	# venv/bin/pip install -r requirements.txt # too slow
	# UV_PROJECT_ENVIRONMENT=venv uv add -r requirements.txt
	# the most useful feature of uv
	UV_PYTHON=venv uv pip install -r requirements.txt
	@echo "deps installed"
	@touch $@

upgrade-deps:
	venv/bin/pur -r requirements.txt --force --skip=$(FREEZE_PY_REQ)

venv: venv/.venv_created

venv/.venv_created: Makefile
	# $(PYTHON_BIN) -mvenv ./venv
	# the 2nd most useful feature of uv
	uv venv --python=$(PYTHON_VER) venv
	@touch $@

dist: .PHONY
	rm -rvf dist
	venv/bin/python3 -m build --sdist

.PHONY:
