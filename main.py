#!/usr/bin/env python

import os
import confuse
import pandas as pd
import numpy as np
from flask import Flask
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)
cfg = confuse.Configuration('JiraMetricsEazybi', __name__)


class Eazybi(Resource):
    def __init__(self):
        return

    def get(self):
        cfg.set_file('../secrets/Vulcano')
        result = self.metrics()
        # result.to_csv('result.csv', index_label='issuetype')
        return result.to_json(orient="table")

    def get_eazybi_report(self, report_url):
        dictio = pd.read_csv(report_url, delimiter=',', parse_dates=['Date'])
        dictio.columns = ['date', 'key', 'issuetype', 'cycletime']
        dictio = dictio.replace(str(cfg['Issuetype']['Story']), 'Story')
        dictio = dictio.replace(str(cfg['Issuetype']['Bug']), 'Bug')
        dictio = dictio.replace(str(cfg['Issuetype']['Task']), 'Task')
        return dictio

    def calc_cycletime_percentile(self, kanban_data, percentile=None):
        """Calculate cycletime percentiles on cfg with all dict entries"""
        if kanban_data.empty is False:
            if percentile is not None:
                issuetype = kanban_data.groupby(
                    'issuetype').cycletime.quantile(
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

    def calc_throughput(self, kanban_data, start_date=None, end_date=None):
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
            throughput['All'] = 0
            if 'Story' in throughput:
                throughput['All'] += throughput.Story
            if 'Bug' in throughput:
                throughput['All'] += throughput.Bug
            if 'Task' in throughput:
                throughput['All'] += throughput.Task
            if throughput.empty is False:
                date_range = pd.date_range(
                    start=throughput.date.min(),
                    end=throughput.date.max()
                )
                throughput = throughput.set_index(
                    'date'
                ).reindex(date_range).fillna(0).astype(int).rename_axis('Date')
            return throughput

    def run_simulation(self, throughput, simul=None, simul_days=None):
        """Run monte carlo simulation with the result of how many itens will
        be delivered in a set of days

        Parameters
        ----------
            throughput : dataFrame
                throughput base values of the simulation
            simul : integer
                number of simulations
            simul_days : integer
                days to run the simulation
        """
        if simul is None:
            simul = cfg['Montecarlo']['Simulations'].get()
        if simul_days is None:
            simul_days = cfg['Montecarlo']['Simulation_days'].get()

        mc = None
        for source in throughput.columns.values.tolist():
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
                    result_index = distribution['Probability'].sub(
                        percentil
                        ).abs().idxmin()
                    mc_results['montecarlo '+str(percentil)+'%'] = \
                        distribution.loc[result_index, 'Items']
                if mc is None:
                    mc = pd.DataFrame.from_dict(
                        mc_results, orient='index', columns=[source]
                        ).transpose()
                else:
                    temp_mc = pd.DataFrame.from_dict(
                        mc_results, orient='index', columns=[source]
                        ).transpose()
                    mc = pd.concat([mc, temp_mc])
            else:
                return None
        return mc

    def calc_simul_days(self):
        start = cfg['Montecarlo']['Simulation Start Date'].get()
        end = cfg['Montecarlo']['Simulation End Date'].get()
        return (end - start).days

    def metrics(self):
        report_url = str(cfg['Report_URL'])
        kanban_data = self.get_eazybi_report(report_url)
        ct = self.calc_cycletime_percentile(kanban_data)
        tp = self.calc_throughput(kanban_data)
        mc = self.run_simulation(tp)
        result = ct.merge(mc, left_index=True, right_index=True)
        return result


class HelloWorld(Resource):
    def get(self):
        return {'about': 'Hello World!'}


api.add_resource(HelloWorld, '/')
api.add_resource(Eazybi, '/eazybi')

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
