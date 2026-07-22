# Locked Model Artifacts — NS-XIDS

**Status: LOCKED.** These six files together are the deployable ANN stage of the
system. Do not regenerate individual files separately (e.g. re-fitting only the
scaler) — they must always be replaced as a matched set from the same training run.

| File | Purpose |
|---|---|
| `ann_model.keras` | Trained Keras model. Input: 35 scaled features. Output: softmax over 6 classes. |
| `scaler.pkl` | `StandardScaler` fitted on `X_train` only (post leakage-fix). Required before every prediction. |
| `label_encoder.pkl` | `LabelEncoder` mapping model output index -> class name. |
| `feature_names.pkl` | Ordered list of the 35 feature names the model expects. Live feature extraction MUST produce a vector in this exact order. |
| `iqr_bounds.pkl` | Per-feature `(lower, upper)` clip bounds computed on `X_train` only. Must be applied to raw features BEFORE scaling. |
| `shap_background.pkl` | 50-row background sample used to initialize the SHAP explainer consistently with training. |

## Required inference order

```
raw feature dict (35 named values)
   -> reorder into feature_names.pkl order
   -> clip each column with iqr_bounds.pkl (raw scale)
   -> scaler.transform()  (scaler.pkl)
   -> model.predict()     (ann_model.keras)
   -> label_encoder.inverse_transform() on argmax
```

See `backend/ml/predict.py` for the reference implementation.

## Model facts

- 6 classes: `BENIGN, Brute_Force, DDoS, DoS Hulk, DoS_Attack, PortScan`
- 35 input features (CICIDS2017-derived flow statistics, no payload inspection)
- Architecture: `35 -> 70 -> 140 -> 70 -> 35 -> 6`, ReLU + Dropout(0.3), softmax output
- Test-set per-class precision/recall/F1: ~0.99-1.00 across all 6 classes (see `training/train_ann_model.ipynb` for the full classification report)

## Known, documented limitation

6 of the 35 features are clipped to a constant `0` by `iqr_bounds.pkl` and therefore
carry **no signal** to the model: `Fwd PSH Flags`, `FIN Flag Count`, `RST Flag Count`,
`URG Flag Count`, `Active Std`, `Idle Std`. This is a known effect of applying
IQR-based outlier clipping to sparse/binary count columns. It does not need to be
fixed before using this model, but **symbolic reasoning rules should not be written
against these 6 features** — they will never vary.

## Provenance

Trained from `datasets/Combined_Dataset.csv` (CICIDS2017-derived). See
`training/train_ann_model.ipynb` for the full, leakage-corrected preprocessing
and training pipeline.
