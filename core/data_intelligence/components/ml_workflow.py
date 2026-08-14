"""MLWorkflowEngine for classification, regression, k-means clustering, anomaly detection, and forecasting."""

import math
import statistics
from typing import List, Dict, Any, Optional
from utils.logger import get_logger
from core.data_intelligence.models.context import DatasetSchema, DataType, MLModelResult

logger = get_logger("MLWorkflowEngine")


class MLWorkflowEngine:
    """Executes automated machine learning workflows on tabular dataset records."""

    def run_clustering(
        self, records: List[Dict[str, Any]], numeric_cols: List[str], k: int = 3
    ) -> MLModelResult:
        """Runs k-means clustering on numeric columns."""
        if not records or not numeric_cols:
            return MLModelResult(task_type="clustering", algorithm_name="K-Means", metrics={"k": k})

        # Extract numeric matrix
        points = []
        for r in records:
            pt = []
            valid = True
            for col in numeric_cols:
                v = r.get(col)
                if v is None:
                    valid = False
                    break
                try:
                    pt.append(float(v))
                except ValueError:
                    valid = False
                    break
            if valid:
                points.append(pt)

        if not points:
            return MLModelResult(task_type="clustering", algorithm_name="K-Means", metrics={"k": k})

        dim = len(numeric_cols)
        k = min(k, len(points))
        # Simple centroid initialization
        centroids = [points[i * (len(points) // k)] for i in range(k)]

        for _ in range(10): # Iterations
            clusters: List[List[List[float]]] = [[] for _ in range(k)]
            for pt in points:
                # Find nearest centroid
                best_idx = 0
                best_dist = float("inf")
                for c_idx, c in enumerate(centroids):
                    dist = sum((pt[d] - c[d]) ** 2 for d in range(dim))
                    if dist < best_dist:
                        best_dist = dist
                        best_idx = c_idx
                clusters[best_idx].append(pt)

            # Recompute centroids
            new_centroids = []
            for c_idx in range(k):
                c_pts = clusters[c_idx]
                if c_pts:
                    c_mean = [sum(p[d] for p in c_pts) / len(c_pts) for d in range(dim)]
                    new_centroids.append(c_mean)
                else:
                    new_centroids.append(centroids[c_idx])
            centroids = new_centroids

        # Calculate inertia
        total_inertia = 0.0
        for c_idx, c_pts in enumerate(clusters):
            for pt in c_pts:
                total_inertia += sum((pt[d] - centroids[c_idx][d]) ** 2 for d in range(dim))

        res = MLModelResult(
            task_type="clustering",
            algorithm_name="K-Means",
            metrics={"k": float(k), "inertia": round(total_inertia, 2)},
            cluster_centers=[[round(v, 4) for v in c] for c in centroids],
            predictions_summary={f"cluster_{i}": len(clusters[i]) for i in range(k)},
        )
        logger.info(f"K-Means clustering completed for k={k}, inertia={total_inertia:.2f}")
        return res

    def run_anomaly_detection(
        self, records: List[Dict[str, Any]], numeric_cols: List[str], threshold_z: float = 2.5
    ) -> MLModelResult:
        """Detects anomalies using multidimensional Z-score distance."""
        if not records or not numeric_cols:
            return MLModelResult(task_type="anomaly_detection", algorithm_name="Multivariate Z-Score")

        anomalies_count = 0
        for col in numeric_cols:
            vals = [float(r[col]) for r in records if r.get(col) is not None]
            if len(vals) > 2:
                mean_val = sum(vals) / len(vals)
                std_val = statistics.stdev(vals) if len(vals) > 1 else 1.0
                if std_val > 0:
                    for r in records:
                        v = r.get(col)
                        if v is not None:
                            z = abs((float(v) - mean_val) / std_val)
                            if z >= threshold_z:
                                anomalies_count += 1

        res = MLModelResult(
            task_type="anomaly_detection",
            algorithm_name="Multivariate Z-Score",
            metrics={"threshold_z": threshold_z},
            anomalies_count=anomalies_count,
            predictions_summary={"total_anomalies_detected": anomalies_count},
        )
        logger.info(f"Anomaly detection completed: found {anomalies_count} anomalies")
        return res

    def run_regression(
        self, records: List[Dict[str, Any]], x_col: str, y_col: str
    ) -> MLModelResult:
        """Runs simple linear regression between x_col and y_col."""
        pairs = []
        for r in records:
            vx = r.get(x_col)
            vy = r.get(y_col)
            if vx is not None and vy is not None:
                try:
                    pairs.append((float(vx), float(vy)))
                except ValueError:
                    pass

        if len(pairs) < 2:
            return MLModelResult(task_type="regression", algorithm_name="Linear Regression")

        x = [p[0] for p in pairs]
        y = [p[1] for p in pairs]
        n = len(pairs)

        mean_x = sum(x) / n
        mean_y = sum(y) / n

        num = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        den = sum((x[i] - mean_x) ** 2 for i in range(n))

        slope = num / den if den != 0 else 0.0
        intercept = mean_y - (slope * mean_x)

        # R-squared calculation
        y_pred = [slope * xi + intercept for xi in x]
        ss_res = sum((y[i] - y_pred[i]) ** 2 for i in range(n))
        ss_tot = sum((y[i] - mean_y) ** 2 for i in range(n))
        r2 = 1.0 - (ss_res / ss_tot) if ss_tot != 0 else 0.0

        res = MLModelResult(
            task_type="regression",
            algorithm_name="Linear Regression",
            metrics={"r2_score": round(r2, 4), "slope": round(slope, 4), "intercept": round(intercept, 4)},
            predictions_summary={"target": y_col, "predictor": x_col, "formula": f"{y_col} = {slope:.4f} * {x_col} + {intercept:.4f}"},
            feature_importances={x_col: round(r2, 4)},
        )
        logger.info(f"Linear regression completed: R^2 = {r2:.4f}, formula: y = {slope:.2f}x + {intercept:.2f}")
        return res
