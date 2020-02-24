#!/usr/bin/env python
# Module for testing significance of results. Requires Python 3, statsmodels, &
# related packages to be installed

import os
import sys
assert sys.version_info.major >= 3

import numpy as np
import pandas as pd
import researchpy as rp
import statsmodels.api as sm
import scipy.stats as spstats

from statsmodels.formula import api as smapi
from statsmodels.stats import multicomp


def cronbach_alpha(scores):
    """Given data of the form (scores x dimension) calculate the alpha across
    dimensions"""
    scores = scores.T
    var = scores.var(axis=1, ddof=1)
    total = scores.sum(axis=0)
    # Debug prints
    # print(var.sum())
    # print(total.var(ddof=1))
    # print(total[:])
    # print(var)
    nscores = len(scores)
    return nscores / (nscores-1.0) * (1 - var.sum()/total.var(ddof=1))


def test_significance(df, dependent_var, *independent_vars, logit_model=False, correction_method='bonf'):
    """
    Test the significance of independent vars on the dependent var and output
    the complete results of each step. This doesn't let us tune as many
    parameters as we might want to. (Don't use this generally)

    Args:
        df: DataFrame
        dependent_var: The name of the dependent variable column in df
        independent_vars: Array of independent variable columns in df

    Returns:
        output (str) : A string to print the results of each test
        results (dict) : A dictionary of results corresponding to each test
    """
    ALPHA = 0.05    # Used for diagnostic tests

    assert len(independent_vars) <= 3, "Cannot handle more than 3 factors yet"

    output = ''
    results = {
        'multicollinearity': False,
        'homoskedastic': True,
        'normal_distribution': True,
    }

    # First add the summary data
    summary_df = rp.summary_cont(df.groupby(list(independent_vars))[dependent_var])
    summary_df['median'] = df.groupby(list(independent_vars))[dependent_var].median()
    output += f'Summary:\n{summary_df}\n\n'
    results['summary'] = summary_df

    # Get the OLS model def. The main effects, then the 2 term interactions, and
    # then the 3 term interactions
    model_spec = f"{dependent_var} ~ {' + '.join([f'C({v})' for v in independent_vars])} "
    if len(independent_vars) > 1:
        for i, v1 in enumerate(independent_vars):
            for j, v2 in enumerate(independent_vars[i+1:]):
                model_spec += f'+ C({v1}):C({v2}) '

    if len(independent_vars) > 2:
        model_spec += f"+ {':'.join([f'C({v})' for v in independent_vars])}"

    # Then create the model and fit the data
    if not logit_model:
        model = smapi.ols(model_spec, data=df)
    else:
        # model = smapi.logit(model_spec, data=df)
        model = smapi.glm(model_spec, data=df, family=sm.families.Binomial())
    model_results = model.fit()
    output += f"{model_results.summary()}\n\n"
    results['initial'] = model_results

    # Check for normality
    if not logit_model:
        w, pvalue = spstats.shapiro(model_results.resid)
        output += f'Shapiro-Wilk test: {w, pvalue}\n\n'
        results['shapiro'] = (w, pvalue,)
        if pvalue < ALPHA:
            output += 'NON NORMAL detected. Do something else\n\n'
            results['normal_distribution'] = False

    # Check for homoskedasticity based on the normality test
    if not logit_model:
        unique_values = df.groupby(list(independent_vars)).size().reset_index().rename(columns={0: 'count'})
        hs_test_data = []
        for row in unique_values.itertuples(index=False):
            if len(independent_vars) > 1:
                selectors = [(df[v] == getattr(row, v)) for v in independent_vars]
                row_selector = np.logical_and(*selectors[:2])
                if len(independent_vars) > 2:
                    row_selector = np.logical_and(row_selector, selectors[2])
            else:
                v = independent_vars[0]
                row_selector = df[v] == getattr(row, v)
            hs_test_data.append(df.loc[row_selector, dependent_var])
        assert len(hs_test_data) == unique_values.shape[0]

        if results['normal_distribution']:
            w, pvalue = spstats.bartlett(*hs_test_data)
            output += f'Bartlett test: {w, pvalue}\n\n'
            results['bartlett'] = (w, pvalue,)
        else:
            w, pvalue = spstats.levene(*hs_test_data)
            output += f'Levene test: {w, pvalue}\n\n'
            results['levene'] = (w, pvalue,)
        if pvalue < ALPHA:
            output += 'HETEROSKEDASTICITY detected. Do something else\n\n'
            results['homoskedastic'] = False

        # Check that the condition number is reasonable
        if model_results.diagn['condno'] > 20:
            output += f'MULTICOLLINEARITY detected. Do something else\n\n'
            results['multicollinearity'] = True

    # If we are normal, non-multicollinear, and homoskedastic, perform ANOVA
    # and then multiple comparisons using Tukey's HSD. If heteroskedastic, then
    # we should use robust regression. Else, use a non-parametric test

    # TODO: Perhaps we should look into using the Wald test instead?
    # https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.RegressionResults.wald_test.html
    if results['normal_distribution'] and results['homoskedastic'] and not logit_model:
        o, r = test_using_anova(model, model_results, True, df, dependent_var, *independent_vars)
        output += o
        results.update(r)

    elif results['normal_distribution'] and not logit_model:
        model = smapi.rlm(model_spec, data=df)
        rlm_results = model.fit()
        output += f"{rlm_results.summary()}\n\n"
        results['rlm'] = rlm_results

        o, r = test_using_anova(model, rlm_results, False, df, dependent_var, *independent_vars)
        output += o
        results.update(r)

    elif not logit_model:
        o, r = test_using_kruskal(df, dependent_var, *independent_vars, correction_method=correction_method)
        output += o
        results.update(r)

    # Return the outputs
    return output, results


def augment_anova_table(aov):
    """
    Given an ANOVA table from statsmodels, add some extra info to it
    """
    aov['mean_sq'] = aov[:]['sum_sq'] / aov[:]['df']
    aov['eta_sq'] = aov[:-1]['sum_sq'] / np.sum(aov['sum_sq'])
    aov['omega_sq'] = (aov[:-1]['sum_sq'] - (aov[:-1]['df'] * aov['mean_sq'][-1])) /\
                      (np.sum(aov['sum_sq']) + aov['mean_sq'][-1])
    cols = ['sum_sq', 'df', 'mean_sq', 'F', 'PR(>F)', 'eta_sq', 'omega_sq']
    aov = aov[cols]
    return aov


def test_using_anova(model, model_results, homoskedastic, df, dependent_var, *independent_vars):
    """
    Generate and ANOVA table and test the results using that
    """
    output = ''
    results = {}

    aov_table = sm.stats.anova_lm(model_results, typ=2, robust=None if homoskedastic else 'hc3')
    aov_table = augment_anova_table(aov_table)
    output += f"ANOVA\n{aov_table}\n\n"
    results['anova'] = aov_table

    # Perform multiple comparisons
    mc = multicomp.MultiComparison(df[dependent_var], df.loc[:, independent_vars].astype(str).agg(','.join, axis=1))
    mc_results = mc.tukeyhsd()
    output += f"Tukey's HSD:\n{mc_results}\n\n"
    results['multiple'] = mc_results

    return output, results


def test_using_kruskal(df, dependent_var, *independent_vars, correction_method='bonf'):
    """
    Test for the significance of factors using the non-parametric Kruskal-Wallis
    test followed by a Mann-Whitney U test with Bonferroni correction
    """
    output = ''
    results = {}

    unique_values = df.groupby(list(independent_vars)).size().reset_index().rename(columns={0: 'count'})
    test_data = []
    for row in unique_values.itertuples(index=False):
        if len(independent_vars) > 1:
            selectors = [(df[v] == getattr(row, v)) for v in independent_vars]
            row_selector = np.logical_and(*selectors[:2])
            if len(independent_vars) > 2:
                row_selector = np.logical_and(row_selector, selectors[2])
        else:
            v = independent_vars[0]
            row_selector = df[v] == getattr(row, v)
        test_data.append(df.loc[row_selector, dependent_var])
    assert len(test_data) == unique_values.shape[0]

    test_results = spstats.kruskal(*test_data)
    output += f"Kruskal-Wallis test:\n{test_results.statistic}, {test_results.pvalue}\n\n"
    results['kruskal'] = test_results

    # Perform multiple comparisons with Bonferroni correction
    try:
        mc = multicomp.MultiComparison(df[dependent_var], df.loc[:, independent_vars].astype(str).agg(','.join, axis=1))
        mc_results = mc.allpairtest(spstats.mannwhitneyu, method=correction_method)
        output += f"Pairwise Mann-Whitney U:\n{mc_results[0]}\n\n"
        results['multiple'] = mc_results[0]
    except Exception as e:
        print(e)

    return output, results
