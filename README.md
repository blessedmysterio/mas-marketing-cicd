# Multi-Agent Simulation of Marketing Situations — CI/CD

Agent-based model of brand competition on a scale-free (Barabási–Albert) consumer network,
packaged with a full DevOps toolchain: **pytest → Docker → Jenkins → Docker Hub → Kubernetes (Minikube)**.

| Scenario | Treatment vs. control | Typical result (30 paired runs) |
|---|---|---|
| S1 | Price war: brands A and B both raise advertising | not significant |
| S2 | Seed 10 **hubs** vs. 10 **random** consumers with brand A | significant, hubs win |
| S3 | Seed 10 hubs vs. **mass advertising** of equal budget | significant, hubs win |

## Repository layout

```
src/mas_marketing/   network.py · model.py · experiment.py · __main__.py (CLI)
tests/               23 unit tests (network, model, experiments, CLI)
Dockerfile           multi-stage: builder -> test (runs pytest) -> runtime (non-root)
Jenkinsfile          CI/CD pipeline (lint, tests, build, smoke test, push, deploy)
jenkins/             Jenkins-as-code: Dockerfile, plugins.txt, casc.yaml, docker-compose
k8s/                 namespace, PVC and batch Job for Minikube
.github/workflows/   the same CI on GitHub Actions (alternative)
```

## 1. Run locally

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt -e .
pytest                                                  # 23 tests
python -m mas_marketing --runs 30 --out results         # S1, S2, S3
```

## 2. Run in Docker

```bash
docker build --target test -t mas-marketing:test .      # tests run during the build
docker build -t mas-marketing:latest .
docker run --rm -v "$PWD/results:/app/results" mas-marketing:latest
docker run --rm mas-marketing:latest --scenario S2 --runs 10   # custom arguments
```

## 3. Jenkins CI (local, ~10 minutes)

Prerequisites: Docker Desktop (or Docker Engine), Git, a GitHub repo with this code.

```bash
cd jenkins
cp .env.example .env            # set admin password, REPO_URL, Docker Hub user + access token
docker compose up -d --build    # first build takes a few minutes
```

Open http://localhost:8080, log in with the credentials from `.env`.
The job **mas-marketing-ci** is created automatically from `casc.yaml`.
Click **Build with Parameters** → **Build** for the first run (it registers the triggers).

**Runs on every commit:** the pipeline polls Git every 2 minutes (`pollSCM`).
For instant builds, expose Jenkins with `ngrok http 8080` and add a GitHub webhook
`https://<ngrok-url>/github-webhook/` (content type `application/json`, event *push*).

Docker Hub token: hub.docker.com → Account settings → Personal access tokens → *Read & Write*.
If you skip Docker Hub, untick `PUSH_IMAGE` (the deploy stage is then skipped too).

## 4. CD to Kubernetes (Minikube, bonus)

```bash
minikube start --driver=docker
cd jenkins && ./minikube-kubeconfig.sh      # writes jenkins/kubeconfig (git-ignored)
docker compose -f docker-compose.yml -f docker-compose.cd.yml up -d
```

Run the job with `DEPLOY_K8S` ticked. The pipeline recreates the `mas-simulation` Job in
namespace `mas-research`, waits for completion and prints the simulation output. Check manually:

```bash
kubectl -n mas-research get jobs,pods,pvc
kubectl -n mas-research logs job/mas-simulation
```

## Pipeline stages

`Checkout → Setup Python → Lint → Unit tests (JUnit + coverage) → Build Docker image
→ Smoke test container → Push to Docker Hub → Deploy to Minikube`

## Author

Nadir — MSc Computer Science & Engineering, Astana IT University · ORCID 0009-0006-3348-3901
