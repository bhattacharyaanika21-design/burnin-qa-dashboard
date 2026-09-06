# Burn-In Screening QA Dashboard

Streamlit dashboard matching the project brief's "Dashboard UI Views":
Module A Inspector, Module B Forecast Visualizer, and an Explainability panel,
plus a full sortable/downloadable results table.

## 1. Generate the data

Run `module_a_and_b_mosfet_real_data.ipynb` in Colab (or locally) end to end.
The last two cells save and download three files:

- `module_a_results.csv`
- `module_b_results.csv`
- `all_curves.csv`

Put all three inside this folder's `data/` subfolder (replacing the
placeholder text file there).

## 2. Install dependencies

```
pip install -r requirements.txt
```

## 3. Run it

```
streamlit run app.py
```

This opens the dashboard in your browser at `http://localhost:8501`. Use the
sidebar to filter by status (NORMAL / WATCH / CRITICAL) and pick a component
to inspect across all three tabs.

## Running from Colab instead of your own machine

If you'd rather not install Python locally, you can run the dashboard from
Colab itself:

1. Upload `app.py`, `requirements.txt`, and the `data/` folder (with your
   three CSVs) into your Colab session's file storage.
2. In a Colab cell:
   ```
   !pip install -q streamlit plotly
   !npm install -q localtunnel
   !streamlit run app.py &>/content/logs.txt &
   !npx localtunnel --port 8501
   ```
3. Click the URL localtunnel prints. It will ask for a "tunnel password" --
   run `!curl https://loca.lt/mytunnelpassword` in another cell and paste
   that value in.

The local `streamlit run` route (steps 1-3 above) is simpler and is what
you'll want for a hackathon demo -- do that first and only use the Colab
route if you don't have Python available on the machine you're demoing from.
