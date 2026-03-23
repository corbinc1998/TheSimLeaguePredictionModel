# Resources

Reference material used in building the config file (config.py).

---

## Prediction Model

- [How Our NFL Predictions Work — FiveThirtyEight](https://fivethirtyeight.com/methodology/how-our-nfl-predictions-work/)
  Methodology behind FiveThirtyEight's NFL Elo model — informed the Elo rating system, K factor tuning, home field advantage constant, and playoff weighting.

- [Concept Drift and Model Decay in Machine Learning — Towards Data Science](https://towardsdatascience.com/concept-drift-and-model-decay-in-machine-learning-a98a809ea8d4/)
  Informed the decision to use recency decay on historical stats and H2H matchups rather than treating all seasons equally.

---

## Elo Rating System

- [Elo Rating System — Wikipedia](https://en.wikipedia.org/wiki/Elo_rating_system)
  Comprehensive overview of the Elo system including the math behind expected outcomes, K factor, and how it has been adapted for sports beyond chess.

- [Arpad Elo — Wikipedia](https://en.wikipedia.org/wiki/Arpad_Elo)
  Background on the creator of the system — useful for understanding the original intent and limitations Elo himself acknowledged.

---

## Logistic Regression

- [Logistic Regression — IBM](https://www.ibm.com/think/topics/logistic-regression)
  Clear explainer on logistic regression, the sigmoid function, and why it is preferred over linear regression for binary outcomes like win/loss prediction.

- [Logistic Regression in Machine Learning — GeeksforGeeks](https://www.geeksforgeeks.org/machine-learning/understanding-logistic-regression/)
  Covers the sigmoid function, decision thresholds, and the relationship between the logistic scale factor and probability output — directly relevant to `LOGISTIC_SCALE` in config.

---

## Model Calibration & Log Loss

- [Machine Learning for Sports Betting: Should Model Selection Be Based on Accuracy or Calibration? — arXiv](https://arxiv.org/abs/2303.06021)
  Research paper using NBA data showing that optimising for calibration rather than accuracy leads to significantly better outcomes — directly informs why log loss matters more than raw accuracy for this model.

- [Probability Calibration in Machine Learning — Train in Data](https://www.blog.trainindata.com/probability-calibration-in-machine-learning/)
  Explains Brier score, log loss, and calibration curves — the tools you will use in `evaluate.py` to check whether a 60% prediction actually wins 60% of the time.