#!/usr/bin/env python

import os
import confuse
import pandas as pd
import numpy as np
from pprint import pprint


cfg = confuse.Configuration('JiraMetricsEazybi', __name__)


def get_eazybi_report(report_url):
    dictio = pd.read_csv(report_url, delimiter=',', parse_dates=['Date'])
    dictio.columns = ['date', 'key', 'issuetype', 'cycletime']
    dictio = dictio.replace(str(cfg['Issuetype']['Story']), 'Story')
    dictio = dictio.replace(str(cfg['Issuetype']['Bug']), 'Bug')
    dictio = dictio.replace(str(cfg['Issuetype']['Task']), 'Task')
    return dictio

def calc_cycletime_percentile(kanban_data, percentile=None):
    """Calculate cycletime percentiles on cfg with all dict entries"""
    if kanban_data.empty is False:
        if percentile is not None:
            issuetype = kanban_data.groupby('issuetype').cycletime.quantile(
                percentile / 100)
            issuetype['Total'] = kanban_data.cycletime.quantile(
                percentile / 100)
            issuetype = issuetype.apply(np.ceil)
            return issuetype
        else:
            for cfg_percentile in cfg['Cycletime']['Percentiles'].get():
                cycletime = kanban_data.groupby(
                    'issuetype').cycletime.quantile(
                    cfg_percentile / 100)
                cycletime['Total'] = kanban_data.cycletime.quantile(
                    cfg_percentile / 100)


def calc_throughput(kanban_data, start_date=None, end_date=None):
    """Change the pandas DF to a Troughput per day format"""
    if start_date is not None and 'date' in kanban_data.columns:
        kanban_data = kanban_data[~(
            kanban_data['date'] < start_date)]
    if end_date is not None and 'date' in kanban_data.columns:
        kanban_data = kanban_data[~(
            kanban_data['date'] > end_date)]
    if kanban_data.empty is False:
        # Reorganize DataFrame
        throughput = pd.crosstab(
            kanban_data.date, kanban_data.issuetype, colnames=[None]
        ).reset_index()
        # Sum Throughput per day
        throughput['Throughput'] = 0
        if 'Story' in throughput:
            throughput['Throughput'] += throughput.Story
        if 'Bug' in throughput:
            throughput['Throughput'] += throughput.Bug
        if 'Task' in throughput:
            throughput['Throughput'] += throughput.Task
        if throughput.empty is False:
            date_range = pd.date_range(
                start=throughput.date.min(),
                end=throughput.date.max()
            )
            throughput = throughput.set_index(
                'date'
            ).reindex(date_range).fillna(0).astype(int).rename_axis('Date')
        return throughput


def metrics():
    report_url = str(cfg['Report_URL'])
    simulations = cfg['Montecarlo']['Simulations'].get()
    simulation_days = cfg['Montecarlo']['Simulation_days'].get()
    kanban_data = get_eazybi_report(report_url)
    ct = calc_cycletime_percentile(kanban_data, 85)
    tp = calc_throughput(kanban_data)
    print(tp)
    """
    mc = simulate_montecarlo(
        tp, sources='Throughput',
        simul=simulations,
        simul_days=simulation_days)
    """


def main():
    if os.path.isfile('config.yml'):
        cfg.set_file('config.yml')
        mc = metrics()
        # print(mc)
    else:
        raise Exception("You don't have any valid config files")


if __name__ == "__main__":
    main()
