# ITC-Assignments — Day 9 CI/CD

A `git push` to `main` triggers Jenkins, which runs a Spark job on the Cloudera YARN cluster.

## Sample modifications for jenksin webhook

## Flow

```
git push (main)
   │  GitHub webhook -> http://13.42.152.118:8080/github-webhook/
   ▼
Jenkins pipeline (ITC-Assignments)
   ├── Checkout from GitHub
   ├── Copy src/transformation.py -> Cloudera /tmp   (scp)
   └── spark-submit --master yarn (Java 11)          -> runs on YARN
```
## Noice


## Files
- `Jenkinsfile` — declarative pipeline (checkout -> scp -> spark-submit).
- `src/transformation.py` — sample Spark job; `filter_experienced()` keeps experience > threshold.
- `tests/test_transformation.py` — pytest unit tests for `filter_experienced` (run locally in a venv).
- `conftest.py` — puts repo root on `sys.path` and pins `PYSPARK_PYTHON` to the test interpreter.
## Sreeni Push - check
## Run tests locally
```bash
python3.11 -m venv .venv && . .venv/bin/activate
pip install pyspark==3.5.1 pytest
pytest -q
```

## Notes (dockerized Jenkins on 13.42.152.118)
- SSH key to Cloudera lives at `/var/jenkins_home/.ssh/id_rsa` inside the `jenkins-docker` container.
- `JAVA_HOME=/usr/lib/jvm/java-11` — CDH Spark 2.4.7 injects `--add-opens`, which is fatal on Java 8.
