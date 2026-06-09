FROM python:3.11-slim

WORKDIR /app

# Copy only the manifest first so the heavy dep-install layer is cached
# independently of source changes. This layer only re-runs when pyproject.toml
# changes (i.e. a dependency is added or removed).
COPY pyproject.toml .
RUN python3 -c "
import tomllib
with open('pyproject.toml', 'rb') as f:
    deps = tomllib.load(f)['project']['dependencies']
with open('/tmp/requirements.txt', 'w') as f:
    f.write('\n'.join(deps))
" && pip install --no-cache-dir -r /tmp/requirements.txt

# Source and data are copied after deps so that code edits only invalidate
# these fast layers, not the multi-GB dep install above.
COPY src/ src/
COPY data/private/ data/private/

ENV PYTHONPATH=/app/src

EXPOSE 8080

CMD ["uvicorn", "orchestrator.main:app", "--host", "0.0.0.0", "--port", "8080"]
