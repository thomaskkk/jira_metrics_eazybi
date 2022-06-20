#!/usr/bin/env python

import os
import confuse
import pandas as pd
from flask import Flask
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)
cfg = confuse.Configuration('JiraMetricsEazybi', __name__)


class Eazybi(Resource):
    def __init__(self):
        return

    def get(self):
        if os.path.isfile('secrets/config.yml'):
            cfg.set_file('secrets/config.yml')
            result = self.metrics()
            return result.to_json(orient="table")
        else:
            raise Exception("You don't have any valid config files")

    def metrics(self):
        report_url = str(cfg['Report_URL'])
        kanban_data = self.get_eazybi_report(report_url)
        tp = self.calc_throughput(kanban_data)
        mc = self.run_simulation(tp)
        mc = mc.rename(index={'issues': kanban_data.loc[0]['project']})
        return mc

    def get_eazybi_report(self, report_url):
        dictio = pd.read_csv(report_url, delimiter=',', parse_dates=['Time'])
        dictio.columns = ['project', 'date', 'issue', 'cycletime']
        return dictio

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
                kanban_data.date, columns=['issues'], colnames=[None]
            ).reset_index()
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
        if (throughput is not None):
            dataset = throughput[['issues']].reset_index(drop=True)
            samples = [getattr(dataset.sample(
                n=simul_days, replace=True
            ).sum(), 'issues') for i in range(simul)]
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
                    mc_results, orient='index', columns=['issues']
                    ).transpose()
            else:
                temp_mc = pd.DataFrame.from_dict(
                    mc_results, orient='index', columns=['issues']
                    ).transpose()
                mc = pd.concat([mc, temp_mc])
        else:
            return None
        return mc


class HelloWorld(Resource):
    def get(self):
        return {'about': 'Hello World!'}


api.add_resource(HelloWorld, '/')
api.add_resource(Eazybi, '/eazybi')

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
