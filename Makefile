UV := uv
PYTHON := PYTHONPATH=$(CURDIR) $(UV) run python
NEO4J_CONTAINER ?= fraunhofer-neo4j
NEO4J_IMAGE ?= neo4j:5-community
NEO4J_BOLT_PORT ?= 7687
NEO4J_HTTP_PORT ?= 7474
NEO4J_AUTH ?= neo4j/password
NEO4J_DATA_VOLUME ?= fraunhofer-neo4j-data
NEO4J_DUMPS_DIR ?= $(CURDIR)/neo4j-dumps
GRAPH ?= movies
RUN ?= current
RUNS_DIR ?= outputs/runs
COMPARISON_DIR ?= $(RUNS_DIR)/comparisons
MODEL_DIR ?= $(RUNS_DIR)/$(RUN)/model
EVALUATION_DIR ?= $(RUNS_DIR)/$(RUN)/evaluation
LABEL ?= baseline
HF_REPO_ID ?=
TRAIN_ARGS ?=
EVALUATE_ARGS ?=
ANALYZE_ARGS ?=
SMOKE_ARGS ?=

.PHONY: help install lock run-smoke train evaluate baseline-evaluate analyze-results test-analyze compare-runs upload-model test neo4j-pull neo4j-up neo4j-down neo4j-logs neo4j-status neo4j-download neo4j-import neo4j-reset

help:
	@printf '%s\n' \
	  'install       Install and synchronize Python dependencies with uv' \
	  'lock          Refresh the uv lockfile' \
	  'run-smoke     Test a model, the Text-to-Cypher dataset, and Neo4j' \
	  'train         Fully fine-tune SmolLM2 for RUN=current (e.g. make train RUN=syntax-check-v1)' \
	  'baseline-evaluate  Evaluate the base model for RUN=current (e.g. make baseline-evaluate RUN=syntax-check-v1)' \
	  'evaluate      Evaluate MODEL_DIR for RUN=current (e.g. make evaluate RUN=syntax-check-v1)' \
	  '              Execution example: make evaluate RUN=syntax-check-v1 EVALUATE_ARGS="--execute --execution-graph movies"' \
	  'analyze-results  Analyze LABEL evaluation results (override ANALYZE_ARGS=...)' \
	  'test-analyze  Evaluate and analyze RUN=current (e.g. make test-analyze RUN=syntax-check-v1)' \
	  'compare-runs  Compare every completed run below RUNS_DIR' \
	  'upload-model  Upload MODEL_DIR to HF_REPO_ID (requires HF_TOKEN login)' \
	  'test          Run the Python test suite with uv' \
	  'neo4j-pull    Pull the Neo4j Docker image' \
	  'neo4j-up      Start Neo4j in Docker' \
	  'neo4j-down    Stop and remove the Neo4j container' \
	  'neo4j-logs    Follow Neo4j container logs' \
	  'neo4j-status  Show Neo4j container status' \
	  'neo4j-download GRAPH=movies  Download the selected graph dump' \
	  'neo4j-import GRAPH=movies    Download and replace Neo4j data with the selected graph' \
	  'neo4j-reset   Remove the persistent Neo4j data volume'

install:
	$(UV) sync --all-groups

lock:
	$(UV) lock

run-smoke:
	$(PYTHON) scripts/smoke_test.py $(SMOKE_ARGS)

train:
	$(PYTHON) scripts/train.py --output-dir $(MODEL_DIR) $(TRAIN_ARGS)

baseline-evaluate:
	$(PYTHON) scripts/evaluate.py --output-dir $(EVALUATION_DIR) --label baseline $(EVALUATE_ARGS)

evaluate:
	$(PYTHON) scripts/evaluate.py --model $(MODEL_DIR) --output-dir $(EVALUATION_DIR) --label trained $(EVALUATE_ARGS)

analyze-results:
	$(PYTHON) scripts/analyze_results.py $(EVALUATION_DIR)/$(LABEL)_results.jsonl --output-dir $(EVALUATION_DIR) --prefix $(LABEL) $(ANALYZE_ARGS)

test-analyze: evaluate
	$(PYTHON) scripts/analyze_results.py $(EVALUATION_DIR)/trained_results.jsonl --output-dir $(EVALUATION_DIR) --prefix trained $(ANALYZE_ARGS)

compare-runs:
	$(PYTHON) scripts/compare_runs.py --runs-dir $(RUNS_DIR) --output-dir $(COMPARISON_DIR)

upload-model:
	@test -n "$(HF_REPO_ID)" || (echo 'Set HF_REPO_ID=owner/repository.' >&2; exit 2)
	$(PYTHON) scripts/upload_model.py --model-dir $(MODEL_DIR) --repo-id $(HF_REPO_ID)

test:
	$(UV) run pytest

neo4j-pull:
	docker pull $(NEO4J_IMAGE)

neo4j-up:
	@docker rm --force $(NEO4J_CONTAINER) >/dev/null 2>&1 || true
	docker run --detach --name $(NEO4J_CONTAINER) \
		--publish $(NEO4J_HTTP_PORT):7474 --publish $(NEO4J_BOLT_PORT):7687 \
		--env NEO4J_AUTH=$(NEO4J_AUTH) \
		--volume $(NEO4J_DATA_VOLUME):/data \
		--health-cmd='wget -q --spider http://localhost:7474 || exit 1' \
		--health-interval=10s --health-timeout=5s --health-retries=10 \
		$(NEO4J_IMAGE)

neo4j-down:
	docker rm --force $(NEO4J_CONTAINER)

neo4j-logs:
	docker logs --follow $(NEO4J_CONTAINER)

neo4j-status:
	docker ps --filter name=$(NEO4J_CONTAINER)

neo4j-download:
	@set -eu; \
	mkdir -p "$(NEO4J_DUMPS_DIR)"; \
	case "$(GRAPH)" in \
		movies) dump_file="$(NEO4J_DUMPS_DIR)/movies-50.dump"; url='https://raw.githubusercontent.com/neo4j-graph-examples/movies/main/data/movies-50.dump';; \
		twitter) dump_file="$(NEO4J_DUMPS_DIR)/twitter-v2-50.dump"; url='https://raw.githubusercontent.com/neo4j-graph-examples/twitter-v2/main/data/twitter-v2-50.dump';; \
		fincen) dump_file="$(NEO4J_DUMPS_DIR)/fincen-50.dump"; url='https://raw.githubusercontent.com/neo4j-graph-examples/fincen/main/data/fincen-50.dump';; \
		stackoverflow) dump_file="$(NEO4J_DUMPS_DIR)/stackoverflow-50.dump"; url='https://raw.githubusercontent.com/neo4j-graph-examples/stackoverflow/main/data/stackoverflow-50.dump';; \
		twitch) \
			git lfs version >/dev/null 2>&1 || { echo 'GRAPH=twitch requires git-lfs.' >&2; exit 2; }; \
			if [ ! -d "$(NEO4J_DUMPS_DIR)/twitch-source/.git" ]; then \
				git clone --depth 1 https://github.com/neo4j-graph-examples/twitch.git "$(NEO4J_DUMPS_DIR)/twitch-source"; \
			fi; \
			git -C "$(NEO4J_DUMPS_DIR)/twitch-source" lfs pull; \
			dump_file="$(NEO4J_DUMPS_DIR)/twitch-source/data/twitch-50.dump"; \
			[ "$$(wc -c < "$$dump_file")" -gt 1000000 ] || { echo "Twitch dump was not retrieved from Git LFS: $$dump_file" >&2; exit 1; };; \
		*) echo "Unsupported GRAPH=$(GRAPH). Use movies, twitter, fincen, stackoverflow, or twitch." >&2; exit 2;; \
	esac; \
	if [ "$(GRAPH)" != twitch ]; then \
		curl --fail --location --retry 3 --output "$$dump_file" "$$url"; \
	fi; \
	[ -s "$$dump_file" ] || { echo "Missing dump: $$dump_file" >&2; exit 1; }

neo4j-import: neo4j-download
	@set -eu; \
	case "$(GRAPH)" in \
		movies) dump_file="$(NEO4J_DUMPS_DIR)/movies-50.dump";; \
		twitter) dump_file="$(NEO4J_DUMPS_DIR)/twitter-v2-50.dump";; \
		fincen) dump_file="$(NEO4J_DUMPS_DIR)/fincen-50.dump";; \
		stackoverflow) dump_file="$(NEO4J_DUMPS_DIR)/stackoverflow-50.dump";; \
		twitch) dump_file="$(NEO4J_DUMPS_DIR)/twitch-source/data/twitch-50.dump";; \
		*) echo "Unsupported GRAPH=$(GRAPH)." >&2; exit 2;; \
	esac; \
	docker rm --force $(NEO4J_CONTAINER) >/dev/null 2>&1 || true; \
	docker run --rm \
		--volume "$(NEO4J_DATA_VOLUME):/data" \
		--volume "$$dump_file:/dumps/neo4j.dump:ro" \
		--entrypoint neo4j-admin \
		$(NEO4J_IMAGE) database load neo4j --from-path=/dumps --overwrite-destination=true
	@$(MAKE) --no-print-directory neo4j-up
	@set -eu; \
	for attempt in $$(seq 1 30); do \
		if [ "$$(docker inspect --format '{{.State.Health.Status}}' $(NEO4J_CONTAINER) 2>/dev/null || true)" = healthy ]; then break; fi; \
		[ "$$attempt" -lt 30 ] || { echo 'Neo4j did not become healthy after import.' >&2; exit 1; }; \
		sleep 2; \
	done; \
	auth='$(NEO4J_AUTH)'; \
	docker exec $(NEO4J_CONTAINER) cypher-shell -u "$${auth%%/*}" -p "$${auth#*/}" 'MATCH (n) RETURN count(n) AS node_count;'

neo4j-reset:
	@docker rm --force $(NEO4J_CONTAINER) >/dev/null 2>&1 || true
	docker volume rm $(NEO4J_DATA_VOLUME)
