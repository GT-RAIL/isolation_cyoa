#!/usr/bin/env python
# Plot the data according to the input data and configs

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


# The different plot functions

def plot_data(plot_df, variables_to_plot, out_var, as_subplots=False):
    """
    plot_df: The data frame
    variables_to_plot: A list of dict for the variables to plot.
        Each dictionary in the list is a separate plot, and each
        dictionary sets the configuration of the plot. Required
        keys are `type` for the type of plot and `var`, a tuple
        of the X axes in the plot. Supported types:
        - box (with swarm)
        - bar
        - point
    out_var: The dependent variable variable to plot on the Y axis
    as_subplots: boolean of whether to output a single plot with
        subplots, or multiple separate plots. Default: False
    """
    num_plots = len(variables_to_plot)

    # Setup the axes if we want subplots
    if as_subplots:
        fig, axes = plt.subplots(
            np.ceil(num_plots / 2).astype(int), 2,
            figsize=(10, 5 * np.ceil(num_plots / 2).astype(int))
        )

    for idx, plot_conf in enumerate(variables_to_plot):
        # Check that we can plot this
        if plot_conf.get('hatches') is not None:
            assert plot_conf['type'] in ['box', 'bar']
            assert len(plot_conf['var']) == 1
            assert plot_conf['order'] is not None

        # Read in the X variables
        if len(plot_conf['var']) == 1:
            x_var, hue_var = plot_conf['var'][0], None
        else:
            x_var, hue_var = plot_conf['var']

        # Plot the data
        if plot_conf['type'] == 'box':
            ax = sns.swarmplot(
                x=x_var, y=out_var, hue=hue_var, data=plot_df,
                order=plot_conf.get('order'),
                palette=plot_conf.get('palette'),
                ax=axes[idx // 2, idx % 2] if as_subplots else None,
                dodge=True
            )
            ax = sns.boxplot(
                x=x_var, y=out_var, hue=hue_var, data=plot_df,
                order=plot_conf.get('order'),
                palette=plot_conf.get('palette'),
                ax=axes[idx // 2, idx % 2] if as_subplots else None,
                boxprops=dict(alpha=0.5)
            )
        elif plot_conf['type'] == 'bar':
            ax = sns.barplot(
                x=x_var, y=out_var, hue=hue_var, data=plot_df,
                order=plot_conf.get('order'),
                palette=plot_conf.get('palette'),
                ax=axes[idx // 2, idx % 2] if as_subplots else None
            )
        elif plot_conf['type'] == 'point':
            ax = sns.pointplot(
                x=x_var, y=out_var, hue=hue_var, data=plot_df,
                order=plot_conf.get('order'),
                palette=plot_conf.get('palette'),
                ax=axes[idx // 2, idx % 2] if as_subplots else None,
                dodge=True
            )

        # Add hatches if we can do that
        if plot_conf.get('hatches') is not None:
            arts = ax.patches if plot_conf['type'] == 'bar' else ax.artists
            order = plot_conf['order']
            hatches = plot_conf['hatches']
            for idx, art in enumerate(arts):
                if hatches[order[idx]] is not None:
                    art.set_hatch(hatches[order[idx]])

        # Add legends, etc.
        if hue_var is not None:
            ax.legend(title=hue_var)

        if plot_conf.get('labels'):
            ax.set_xticklabels(plot_conf['labels'])

        plt.sca(ax)
        if plot_conf.get('ylim') is not None:
            plt.ylim(plot_conf['ylim'])

        if plot_conf.get('rotation'):
            plt.xticks(rotation=plot_conf['rotation'])

        # If we are plotting separately, then plot
        if not as_subplots:
            plt.show()

    # If we made subplots, show them all
    if as_subplots:
        plt.show()
