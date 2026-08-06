# Reproducibility — Clean Environment

## Frozen instance

Do **not** regenerate. Verify bits:

```bash
cd 09_artifacts/publication_validation/v1.1.0-INST
python -c "import hashlib,pathlib;print('ok')"
# verify checksums against instances/v1
python - <<'PY'
from pathlib import Path
import hashlib
root = Path(r'../../instances/v1')
for line in Path('checksums/SHA256SUMS.txt').read_text().splitlines():
    h, rel = line.split()[:2]
    p = root / rel
    dig = hashlib.sha256(p.read_bytes()).hexdigest()
    assert dig == h, (rel, dig, h)
print('checksums OK')
PY
```

## Re-run this validation package

```bash
pip install -r requirements.txt
python run_publication_validation.py
```

Expected: JSON/MD under `reports/` regenerated identically modulo timestamps in checksums metadata.

## Requirements

See `requirements.txt` (pandas, numpy, scipy, scikit-learn).

## Seeds

- Data seed: 20260806 (frozen)
- Validation/model seed: 20260806 unless probing model RNG
