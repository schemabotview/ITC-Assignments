import os
import sys

# Pin Spark's driver AND worker to the same interpreter running pytest.
# Without this, a Spark worker can pick up a different system Python
# (e.g. 3.14) than the venv driver (3.11) and fail with PYTHON_VERSION_MISMATCH.
os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
os.environ.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)

# Present at repo root so pytest adds this dir to sys.path,
# making `import src.transformation` work from tests/.
