"""
Machine Learning Engine for Energy Consumption Prediction.
Implements:
1. Linear Regression (Ordinary Least Squares / Ridge)
2. Decision Tree Regressor (Recursive MSE minimization)
3. Random Forest Regressor (Bootstrap Aggregation + Feature Subsampling)
4. Gradient Boosting Regressor (Stage-wise additive residual modeling)
Alongside data preprocessing, train-test splitting, and evaluation metrics (MAE, RMSE, R², MAPE).
"""

import math
import random
import pickle
import numpy as np

# ==========================================
# 1. EVALUATION METRICS
# ==========================================

def mean_absolute_error(y_true, y_pred):
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    return float(np.mean(np.abs(y_true - y_pred)))

def root_mean_squared_error(y_true, y_pred):
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

def r2_score(y_true, y_pred):
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    if ss_tot == 0:
        return 1.0
    return float(1.0 - (ss_res / ss_tot))

def mean_absolute_percentage_error(y_true, y_pred):
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    non_zero = y_true != 0
    if not np.any(non_zero):
        return 0.0
    return float(np.mean(np.abs((y_true[non_zero] - y_pred[non_zero]) / y_true[non_zero])) * 100.0)

def train_test_split(X, y, test_size=0.2, random_state=42):
    np.random.seed(random_state)
    n_samples = len(X)
    indices = np.arange(n_samples)
    np.random.shuffle(indices)
    
    split_idx = int(n_samples * (1 - test_size))
    train_idx = indices[:split_idx]
    test_idx = indices[split_idx:]
    
    return X[train_idx], X[test_idx], y[train_idx], y[test_idx]


# ==========================================
# 2. FEATURE SCALER
# ==========================================

class StandardScaler:
    def __init__(self):
        self.mean_ = None
        self.scale_ = None

    def fit(self, X):
        X = np.array(X, dtype=float)
        self.mean_ = np.mean(X, axis=0)
        self.scale_ = np.std(X, axis=0)
        self.scale_[self.scale_ == 0] = 1.0
        return self

    def transform(self, X):
        X = np.array(X, dtype=float)
        return (X - self.mean_) / self.scale_

    def fit_transform(self, X):
        return self.fit(X).transform(X)


# ==========================================
# 3. LINEAR REGRESSION (Ridge / OLS)
# ==========================================

class LinearRegressionModel:
    def __init__(self, alpha=1e-3):
        self.alpha = alpha
        self.weights = None
        self.bias = None

    def fit(self, X, y):
        X = np.array(X, dtype=float)
        y = np.array(y, dtype=float)
        n_samples, n_features = X.shape

        # Add intercept column
        X_design = np.hstack([np.ones((n_samples, 1)), X])
        I = np.eye(n_features + 1)
        I[0, 0] = 0.0 # Do not regularize bias

        # Closed-form solution: w = (X^T X + alpha*I)^(-1) X^T y
        A = X_design.T @ X_design + self.alpha * I
        b = X_design.T @ y
        w = np.linalg.solve(A, b)

        self.bias = float(w[0])
        self.weights = w[1:]
        return self

    def predict(self, X):
        X = np.array(X, dtype=float)
        return X @ self.weights + self.bias


# ==========================================
# 4. DECISION TREE REGRESSOR
# ==========================================

class TreeNode:
    def __init__(self, feature=None, threshold=None, left=None, right=None, value=None):
        self.feature = feature
        self.threshold = threshold
        self.left = left
        self.right = right
        self.value = value

    @property
    def is_leaf(self):
        return self.value is not None


class DecisionTreeRegressorModel:
    def __init__(self, max_depth=6, min_samples_split=5, max_features=None):
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.max_features = max_features
        self.root = None

    def fit(self, X, y):
        X = np.array(X, dtype=float)
        y = np.array(y, dtype=float)
        self.root = self._build_tree(X, y, depth=0)
        return self

    def _build_tree(self, X, y, depth):
        n_samples, n_features = X.shape

        if depth >= self.max_depth or n_samples < self.min_samples_split or len(np.unique(y)) <= 1:
            return TreeNode(value=float(np.mean(y)))

        # Feature subsampling if requested
        feature_indices = np.arange(n_features)
        if self.max_features is not None and self.max_features < n_features:
            feature_indices = np.random.choice(n_features, self.max_features, replace=False)

        best_feat, best_thresh, best_var_red = None, None, -1.0
        current_variance = np.var(y) * n_samples

        for feat in feature_indices:
            values = np.unique(X[:, feat])
            if len(values) > 20:
                # Subsample thresholds for fast efficient tree construction
                percentiles = np.linspace(5, 95, 15)
                thresholds = np.percentile(values, percentiles)
            else:
                thresholds = (values[:-1] + values[1:]) / 2.0

            for thresh in thresholds:
                left_mask = X[:, feat] <= thresh
                right_mask = ~left_mask

                if np.sum(left_mask) < 2 or np.sum(right_mask) < 2:
                    continue

                y_left, y_right = y[left_mask], y[right_mask]
                var_left = np.var(y_left) * len(y_left)
                var_right = np.var(y_right) * len(y_right)
                var_reduction = current_variance - (var_left + var_right)

                if var_reduction > best_var_red:
                    best_var_red = var_reduction
                    best_feat = feat
                    best_thresh = thresh

        if best_feat is None or best_var_red <= 1e-7:
            return TreeNode(value=float(np.mean(y)))

        left_mask = X[:, best_feat] <= best_thresh
        left_child = self._build_tree(X[left_mask], y[left_mask], depth + 1)
        right_child = self._build_tree(X[~left_mask], y[~left_mask], depth + 1)

        return TreeNode(feature=best_feat, threshold=best_thresh, left=left_child, right=right_child)

    def _predict_single(self, x, node):
        if node.is_leaf:
            return node.value
        if x[node.feature] <= node.threshold:
            return self._predict_single(x, node.left)
        return self._predict_single(x, node.right)

    def predict(self, X):
        X = np.array(X, dtype=float)
        return np.array([self._predict_single(x, self.root) for x in X])


# ==========================================
# 5. RANDOM FOREST REGRESSOR
# ==========================================

class RandomForestRegressorModel:
    def __init__(self, n_estimators=25, max_depth=7, min_samples_split=4, max_features='sqrt', random_state=42):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.max_features = max_features
        self.random_state = random_state
        self.trees = []

    def fit(self, X, y):
        X = np.array(X, dtype=float)
        y = np.array(y, dtype=float)
        np.random.seed(self.random_state)
        n_samples, n_features = X.shape

        if self.max_features == 'sqrt':
            max_feat = max(1, int(np.sqrt(n_features)))
        elif isinstance(self.max_features, int):
            max_feat = min(n_features, self.max_features)
        else:
            max_feat = n_features

        self.trees = []
        for _ in range(self.n_estimators):
            # Bootstrap sample
            boot_idx = np.random.choice(n_samples, n_samples, replace=True)
            X_boot, y_boot = X[boot_idx], y[boot_idx]

            tree = DecisionTreeRegressorModel(
                max_depth=self.max_depth,
                min_samples_split=self.min_samples_split,
                max_features=max_feat
            )
            tree.fit(X_boot, y_boot)
            self.trees.append(tree)
        return self

    def predict(self, X):
        X = np.array(X, dtype=float)
        predictions = np.array([tree.predict(X) for tree in self.trees])
        return np.mean(predictions, axis=0)


# ==========================================
# 6. GRADIENT BOOSTING REGRESSOR
# ==========================================

class GradientBoostingRegressorModel:
    def __init__(self, n_estimators=30, learning_rate=0.1, max_depth=4, min_samples_split=5, random_state=42):
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.random_state = random_state
        self.init_value = 0.0
        self.trees = []

    def fit(self, X, y):
        X = np.array(X, dtype=float)
        y = np.array(y, dtype=float)
        np.random.seed(self.random_state)

        # Initial prediction: mean of targets
        self.init_value = float(np.mean(y))
        y_pred = np.full(len(y), self.init_value, dtype=float)

        self.trees = []
        for _ in range(self.n_estimators):
            # Residuals (negative gradient for MSE loss)
            residuals = y - y_pred

            tree = DecisionTreeRegressorModel(
                max_depth=self.max_depth,
                min_samples_split=self.min_samples_split
            )
            tree.fit(X, residuals)
            self.trees.append(tree)

            # Update predictions
            update = tree.predict(X)
            y_pred += self.learning_rate * update

        return self

    def predict(self, X):
        X = np.array(X, dtype=float)
        y_pred = np.full(len(X), self.init_value, dtype=float)
        for tree in self.trees:
            y_pred += self.learning_rate * tree.predict(X)
        return y_pred
