# PHASE 0C — RUNTIME COMPATIBILITY

## 1. Current environment
- Python: 3.11.9
- scikit-learn: 1.6.1
- NumPy: 1.26.4
- pandas: 2.2.3
- joblib: 1.6.0

## 2. Artifact-reported environment (from MANIFEST)
- Python: 3.12.13
- scikit-learn: 1.6.1
- pandas: 2.3.3
- joblib: 1.5.3
- NumPy: Not explicitly reported, but trained on version >= 2.0.

## 3. Candidate compatible environment
- Python: 3.11.x or 3.12.x
- NumPy: >= 2.0 (Required for BitGenerator compatibility)
- scikit-learn: 1.6.1
- joblib: 1.5.3 (or 1.6.0)

## 4. Tested environments
- **Test Env 1 (Current)**: NumPy 1.26.4
- **Test Env 2 (Venv)**: NumPy 2.4.6, scikit-learn 1.6.1, joblib 1.5.3

## 5. Load results
- Test Env 1 (NumPy 1.x): FAILED (B0, B1, B2)
- Test Env 2 (NumPy 2.x): PASS (B0, B1, B2)

## 6. Exact exceptions
When loading under NumPy 1.26.4:
```python
ValueError: <class 'numpy.random._pcg64.PCG64'> is not a known BitGenerator module.
```
This is a known serialization incompatibility when a model is trained with NumPy 2.x (which refactored its random generators) and loaded in NumPy 1.x.

## 7. Recommended runtime environment
The environment must be upgraded to **NumPy >= 2.0**. Scikit-learn should remain at `1.6.1`.

## 8. Should main backend environment change?
YES. The backend requirements must be explicitly updated to enforce `numpy>=2.0` before Phase 1 testing begins, otherwise the B-models will crash the API.
