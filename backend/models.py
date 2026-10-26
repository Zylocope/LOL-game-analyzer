"""Small estimators, including an explicit correction to Elo log odds."""
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier


class ProbabilityModel:
    def __init__(self, features, family='residual', regularization=.1):
        self.features = features
        self.family = family
        self.regularization = regularization

    def fit(self, frame, target):
        x = frame[self.features].to_numpy(dtype=float)
        y = np.asarray(target, dtype=float)
        self.scale = np.maximum(np.std(x, axis=0), 1e-6)
        z = x / self.scale
        if self.family == 'elo':
            return self
        if self.family == 'residual':
            offset = x[:, 0] * np.log(10) / 400

            def objective(weights):
                logits = offset + z @ weights
                value = np.mean(np.logaddexp(0, logits) - y * logits)
                value += self.regularization * np.dot(weights, weights) / 2
                gradient = z.T @ (expit(logits) - y) / len(y) + self.regularization * weights
                return value, gradient

            result = minimize(objective, np.zeros(z.shape[1]), method='L-BFGS-B', jac=True)
            if not result.success:
                raise RuntimeError(f'Residual fit failed: {result.message}')
            self.weights = result.x
        else:
            if self.family == 'logistic':
                self.estimator = LogisticRegression(C=self.regularization, fit_intercept=False, max_iter=500)
            elif self.family == 'boosted':
                self.estimator = HistGradientBoostingClassifier(max_iter=80, max_leaf_nodes=7,
                    l2_regularization=10, learning_rate=.05, random_state=42,
                    early_stopping=False)
            else:
                raise ValueError(f'Unknown family {self.family}')
            self.estimator.fit(np.concatenate([z, -z]), np.concatenate([y, 1-y]))
        return self

    def predict_proba(self, frame):
        x = frame[self.features].to_numpy(dtype=float)
        if self.family == 'elo':
            probability = expit(x[:, 0] * np.log(10) / 400)
        elif self.family == 'residual':
            probability = expit(x[:, 0] * np.log(10) / 400 + (x/self.scale) @ self.weights)
        else:
            z = x/self.scale
            probability = (self.estimator.predict_proba(z)[:, 1] + 1 - self.estimator.predict_proba(-z)[:, 1]) / 2
        return np.column_stack([1-probability, probability])
