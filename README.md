# Tawseel Parcel API

Contract-first parcel API for the DSC Software Engineering Week 2 task.

## Run

Use Python 3.12 and install the pinned dependencies with `python -m pip install -r requirements.txt`. Start the API with `uvicorn app.api:app --reload`, then open `http://127.0.0.1:8000/docs`.

## Test

Run `python -m pytest -q` from this directory.

The in-memory store belongs to each application instance and is intended for this assignment only.
