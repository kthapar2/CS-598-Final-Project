"""
Model and debiasing evaluation utilities
"""
import numpy as np

import torch

from sklearn.metrics import (average_precision_score, balanced_accuracy_score)
from sklearn.metrics import roc_auc_score, f1_score


def compute_empirical_bias(y_pred, y_true, priv, metric):
    """Evaluates the model's bias empirically on the given data, used by the adversarial intra-processing algorithm"""
    def zero_if_nan(x):
        if isinstance(x, torch.Tensor):
            return 0. if torch.isnan(x) else x
        else:
            return 0. if np.isnan(x) else x

    gtpr_priv = zero_if_nan(y_pred[priv * y_true == 1].mean())
    gfpr_priv = zero_if_nan(y_pred[priv * (1 - y_true) == 1].mean())
    gtnr_priv = zero_if_nan(y_pred[priv * y_true == 0].mean())
    gfnr_priv = zero_if_nan(y_pred[priv * (1 - y_true) == 0].mean())
    mean_priv = zero_if_nan(y_pred[priv == 1].mean())

    gtpr_unpriv = zero_if_nan(y_pred[(1 - priv) * y_true == 1].mean())
    gfpr_unpriv = zero_if_nan(y_pred[(1 - priv) * (1 - y_true) == 1].mean())
    gtnr_unpriv = zero_if_nan(y_pred[(1 - priv) * y_true == 0].mean())
    gfnr_unpriv = zero_if_nan(y_pred[(1 - priv) * (1 - y_true) == 0].mean())
    mean_unpriv = zero_if_nan(y_pred[(1 - priv) == 1].mean())

    if metric == 'spd':
        return mean_unpriv - mean_priv
    elif metric == 'aod':
        return 0.5 * ((gfpr_unpriv - gfpr_priv) + (gtpr_unpriv - gtpr_priv))
    elif metric == 'eod':
        return gtpr_unpriv - gtpr_priv
    elif metric == 'fpr_diff':
        return gfpr_unpriv - gfpr_priv
    elif metric == 'fnr_diff':
        return gfnr_unpriv - gfnr_priv
    elif metric == 'tnr_diff':
        return gtnr_unpriv - gtnr_priv


def compute_accuracy_metrics(preds_vec, labels_vec):
    """Computes predictive performance metrics from the provided predictions and ground truth labels"""
    # AUROC
    roc_auc = roc_auc_score(labels_vec, preds_vec)

    # Average precision score
    average_precision = average_precision_score(labels_vec, preds_vec)

    # Balanced accuracy
    balanced_acc = balanced_accuracy_score(labels_vec, preds_vec)

    # F1-score
    f1_acc = f1_score(labels_vec, preds_vec)

    return roc_auc, average_precision, balanced_acc, f1_acc


def objective_function(bias, performance, lam=0.75):
    """Linear combination objective function by Svani et al. (2020)"""
    return - lam * abs(bias) - (1 - lam) * (1 - performance)


def sharp_objective_function(bias, performance, sharpness=500., epsilon=0.05):
    """Differentiable bias-constrained objective by Svani et al. (2020) with a tunable sharpness parameter"""
    def sigmoid(value, sharpness, epsilon):
        return 1. / (1. + np.exp(sharpness * (np.abs(value) - epsilon)))

    return sigmoid(bias, sharpness, epsilon) * performance


def threshold_objective_function(bias, performance, epsilon=0.05):
    """Thresholded, non-differentiable bias-constrained objective by Savani et al. (2020)"""
    if abs(bias) < epsilon:
        return performance
    else:
        return 0.0


def get_objective(y_pred, y_true, priv, metric, sharpness=500., epsilon=0.05, kind='threshold'):
    """Evaluates the objective function on the provided data"""
    bias = compute_empirical_bias(y_pred, y_true, priv, metric)
    performance = balanced_accuracy_score(y_true, y_pred)
    if kind == 'default':
        objective = objective_function(bias, performance, epsilon)
    elif kind == 'sharp':
        objective = sharp_objective_function(bias, performance, sharpness, epsilon)
    elif kind == 'threshold':
        objective = threshold_objective_function(bias, performance, epsilon)
    else:
        raise ValueError(f'objective function of kind {kind} is not available.')
    return {'objective': objective, 'bias': bias, 'performance': performance}


def get_valid_objective(y_pred, data, config, valid=False, margin=0.00, num_samples=100):
    """Returns validation set average objective function value obtained using bootstrapping"""
    y_val = data.y_valid_valid if valid else data.y_valid
    p_val = data.p_valid_valid if valid else data.p_valid
    indices = np.random.choice(np.arange(y_pred.size), num_samples * y_pred.size, replace=True).reshape(num_samples,
                                                                                                        y_pred.size)
    results = {'objective': [], 'bias': [], 'performance': []}
    for index in indices:
        result = get_objective(y_pred[index], y_val.numpy()[index], p_val[index],
                               config['metric'], config['objective']['sharpness'],
                               config['objective']['epsilon'] - margin, kind='threshold')
        results = {k: v + [result[k]] for k, v in results.items()}
    return {k: np.mean(v) for k, v in results.items()}


def get_test_objective(y_pred, data, config):
    """Returns point-estimate objective function values on the test data"""
    return get_objective(y_pred, data.y_test.numpy(), data.p_test,
                         config['metric'], config['objective']['sharpness'], config['objective']['epsilon'],
                         kind='threshold')


# NOTE: the two methods below are applied directly to arrays and not to the data wrapper object
def get_valid_objective_(y_pred, y_val, p_val, config, margin=0.00, num_samples=100):
    """Returns validation set average objective function value obtained using bootstrapping"""
    indices = np.random.choice(np.arange(y_pred.size), num_samples * y_pred.size, replace=True).reshape(num_samples,
                                                                                                        y_pred.size)
    results = {'objective': [], 'bias': [], 'performance': []}
    for index in indices:
        result = get_objective(y_pred[index], y_val[index], p_val[index], config['metric'],
                               config['objective']['sharpness'], config['objective']['epsilon'] - margin,
                               kind='threshold')
        results = {k: v + [result[k]] for k, v in results.items()}
    return {k: np.mean(v) for k, v in results.items()}


def get_test_objective_(y_pred, y_test, p_test, config):
    """Returns point-estimate objective function values on the test data"""
    return get_objective(y_pred, y_test, p_test,
                         config['metric'], config['objective']['sharpness'], config['objective']['epsilon'],
                         kind='threshold')


def get_best_thresh(scores, threshs, data, config, margin=0.00):
    """Returns the classification threshold maximising the bootstrapped validation objective"""
    objectives = []
    for thresh in threshs:
        valid_objective = get_objective((scores > thresh) * 1., data.y_valid.numpy(), data.p_valid, config['metric'],
                                        config['objective']['sharpness'], config['objective']['epsilon'] - margin)
        objectives.append(valid_objective['objective'])
    return threshs[np.argmax(objectives)], np.max(objectives)


def eval_model_w_data_loaders(model, device, dataloader, dataset_size: int, batch_size: int, forward_args=None):
    """Applies the model to the data points returned by the data loader, returns tensors with the resulting predictions,
    ground truth labels, and protected attributes"""
    val_scores = np.zeros((dataset_size,))
    val_labels = np.zeros((dataset_size,))
    val_prot = np.zeros((dataset_size,))

    with torch.no_grad():
        cnt = 0
        for inputs, labels, attrs in dataloader:
            inputs = inputs.to(device)
            labels = labels.to(device).to(torch.float)
            attrs = attrs.to(device)

            if forward_args is not None:
                outputs = model(inputs, *forward_args)
            else:
                outputs = model(inputs)

            val_scores[cnt * batch_size:(cnt + 1) * batch_size] = outputs[:, 0].cpu().numpy()
            val_labels[
            cnt * batch_size:(cnt + 1) * batch_size] = labels.cpu().numpy()
            val_prot[cnt * batch_size:(cnt + 1) * batch_size] = attrs.cpu().numpy()

            cnt += 1

    return val_scores, val_labels, val_prot
