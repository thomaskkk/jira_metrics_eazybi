#!/usr/bin/env python

import os
import confuse
import pandas as pd
import numpy as np
# from pprint import pprint


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
            issuetype['All'] = kanban_data.cycletime.quantile(
                percentile / 100)
            issuetype = issuetype.apply(np.ceil)
            issuetype = issuetype.astype('int')
            return issuetype
        else:
            cycletime = None
            for cfg_percentile in cfg['Cycletime']['Percentiles'].get():
                temp_cycletime = kanban_data.groupby(
                    'issuetype').cycletime.quantile(
                    cfg_percentile / 100)
                temp_cycletime['All'] = kanban_data.cycletime.quantile(
                    cfg_percentile / 100)
                temp_cycletime = temp_cycletime.rename(
                    'cycletime '+str(cfg_percentile)+'%').\
                    apply(np.ceil).astype('int')
                if cycletime is None:
                    cycletime = temp_cycletime.to_frame()
                else:
                    cycletime = cycletime.merge(
                        temp_cycletime, left_index=True, right_index=True)
            return cycletime


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


def simulate_montecarlo(throughput, sources=None, simul=None, simul_days=None):
    """
    Simulate Monte Carlo

    Parameters
    ----------
        throughput : dataFrame
            throughput base values of the simulation
        sources : dictionary
            sources that the simulations should run on
        simul : integer
            number of simulations
        simul_days : integer
            days to run the simulation
    """
    if sources is None:
        sources = cfg['Montecarlo']['Source'].get()
    if simul is None:
        simul = cfg['Montecarlo']['Simulations'].get()
    if simul_days is None:
        simul_days = calc_simul_days()
    mc = {}
    for source in sources:
        mc[source] = run_simulation(throughput, source, simul, simul_days)
    return mc


def run_simulation(throughput, source, simul, simul_days):
    """Run monte carlo simulation with the result of how many itens will
    be delivered in a set of days """

    if (throughput is not None and source in throughput.columns):
        dataset = throughput[[source]].reset_index(drop=True)
        samples = [getattr(dataset.sample(
            n=simul_days, replace=True
        ).sum(), source) for i in range(simul)]
        samples = pd.DataFrame(samples, columns=['Items'])
        distribution = samples.groupby(['Items']).size().reset_index(
            name='Frequency'
        )
        distribution = distribution.sort_index(ascending=False)
        distribution['Probability'] = (
                100*distribution.Frequency.cumsum()
            ) / distribution.Frequency.sum()
        mc_results = {}
        # Get nearest neighbor result
        for percentil in cfg['Montecarlo']['Percentiles'].get():
            result_index = distribution['Probability'].sub(percentil).abs()\
                .idxmin()
            mc_results['Percentile '+str(percentil)+'%'] = \
                distribution.loc[result_index, 'Items']
        return mc_results
    else:
        return None


def calc_simul_days():
    start = cfg['Montecarlo']['Simulation Start Date'].get()
    end = cfg['Montecarlo']['Simulation End Date'].get()
    return (end - start).days


def metrics():
    report_url = str(cfg['Report_URL'])
    simulations = cfg['Montecarlo']['Simulations'].get()
    simulation_days = cfg['Montecarlo']['Simulation_days'].get()
    kanban_data = get_eazybi_report(report_url)
    ct = calc_cycletime_percentile(kanban_data)
    print(ct)
    tp = calc_throughput(kanban_data)
    mc = run_simulation(
        tp, source='Throughput',
        simul=simulations,
        simul_days=simulation_days)
    print(mc)


def main():
    if os.path.isfile('config.yml'):
        cfg.set_file('config.yml')
        metrics()
    else:
        raise Exception("You don't have any valid config files")


if __name__ == "__main__":
    main()
