# Development

Run the standard-library test suite from the repository root:

```powershell
python -m unittest discover -s tests -p "test_*.py"
python -m scripts.smoke_check
```

No runtime third-party dependencies are required in the initial skeleton.
