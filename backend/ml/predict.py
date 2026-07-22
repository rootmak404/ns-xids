

import os
import joblib
import numpy as np
import pandas as pd
import shap
from tensorflow.keras.models import load_model

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "models")


class IDSPredictor:
    def __init__(self, models_dir: str = MODELS_DIR):
        self.model = load_model(os.path.join(models_dir, "ann_model.keras"))
        self.scaler = joblib.load(os.path.join(models_dir, "scaler.pkl"))
        self.encoder = joblib.load(os.path.join(models_dir, "label_encoder.pkl"))
        self.feature_names = joblib.load(os.path.join(models_dir, "feature_names.pkl"))
        self.iqr_bounds = joblib.load(os.path.join(models_dir, "iqr_bounds.pkl"))
        self.shap_background = joblib.load(os.path.join(models_dir, "shap_background.pkl"))
        self.explainer = shap.Explainer(self.model, self.shap_background)

    def _to_raw_vector(self, feature_dict: dict) -> pd.DataFrame:
        """Build a single-row DataFrame in the exact trained feature order.
        feature_dict must contain RAW (unscaled) flow feature values, e.g.
        {'Destination Port': 80, 'Flow Duration': 1500000, ...}
        """
        missing = [f for f in self.feature_names if f not in feature_dict]
        if missing:
            raise ValueError(f"Missing required raw features: {missing}")
        row = [feature_dict[f] for f in self.feature_names]
        return pd.DataFrame([row], columns=self.feature_names)

    def predict(self, feature_dict: dict, explain: bool = True) -> dict:
        raw = self._to_raw_vector(feature_dict)

        for col in self.feature_names:
            lower, upper = self.iqr_bounds[col]
            raw[col] = raw[col].clip(lower, upper)

        scaled = self.scaler.transform(raw)

        probs = self.model.predict(scaled, verbose=0)[0]
        pred_idx = int(np.argmax(probs))
        pred_class = self.encoder.inverse_transform([pred_idx])[0]
        confidence = float(probs[pred_idx])

        result = {
            "predicted_class": pred_class,
            "confidence": confidence,
            "class_probabilities": {
                cls: float(p) for cls, p in zip(self.encoder.classes_, probs)
            },
            "raw_features": feature_dict,
            "scaled_features": dict(zip(self.feature_names, scaled[0].tolist())),
        }

        if explain:
            shap_values = self.explainer(scaled)
            feature_shap = shap_values.values[0, :, pred_idx]
            evidence = sorted(
                zip(self.feature_names, raw.iloc[0].values, feature_shap),
                key=lambda x: abs(x[2]),
                reverse=True,
            )[:10]
            result["evidence"] = [
                {"feature": f, "value": float(v), "shap_contribution": float(s)}
                for f, v, s in evidence
            ]

        return result


if __name__ == "__main__":
  
    predictor = IDSPredictor()
    example_raw = dict(zip(predictor.feature_names, predictor.scaler.mean_))
    example_raw["Destination Port"] = 80  # override with a realistic raw value
    output = predictor.predict(example_raw)
    print("Predicted class:", output["predicted_class"])
    print("Confidence:", round(output["confidence"] * 100, 2), "%")
    print("Top evidence:")
    for e in output["evidence"][:5]:
        print(f"  {e['feature']}: value={e['value']:.4f}, shap={e['shap_contribution']:+.4f}")
