#!/usr/bin/env python

import os
import confuse
import pandas as pd
from pprint import pprint


cfg = confuse.Configuration('JiraMetricsEazybi', __name__)


def get_eazybi_report(report_url):
    dictio = pd.read_csv(report_url, delimiter=',')
    dictio.columns = ['Date', 'Key', 'IssueType', 'CycleTime']
    return dictio


def metrics():
    report_url = str(cfg['Report_URL'])
    simulations = cfg['Montecarlo']['Simulations'].get()
    simulation_days = cfg['Montecarlo']['Simulation_days'].get()
    kanban_data = get_eazybi_report(report_url)
    print(kanban_data)
    """
    ct = calc_cycletime_percentile(kanban_data, 85)
    tp = calc_throughput(kanban_data)
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
