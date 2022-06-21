#!/usr/bin/env python

import os
import confuse
import pandas as pd
import numpy as np
from datetime import date, timedelta
from flask import Flask
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)
cfg = confuse.Configuration('JiraMetricsEazybi', __name__)


class Eazybi(Resource):
    def __init__(self):
        return

    def get(self, filename):
        if os.path.isfile('secrets/'+str(filename)+'/'+str(filename)+'.yml'):
            cfg.set_file('secrets/'+str(filename)+'/'+str(filename)+'.yml')
            result = self.metrics()
            return result.to_json(orient="table")
        elif os.path.isfile('secrets/'+str(filename)+'/'+str(filename)):
            cfg.set_file('secrets/'+str(filename)+'/'+str(filename))
            result = self.metrics()
            return result.to_json(orient="table")
        else:
            return {"message":  {
                "filename": "You don't have any valid config files", }}

    def metrics(self):
        report_url = self.generate_url()
        kanban_data = self.get_eazybi_report(report_url)
        ct = self.calc_cycletime_percentile(kanban_data)
        today = date.today().strftime("%Y-%m-%d")
        past = date.today() - timedelta(days=cfg['Throughput_range'].get())
        past = past.strftime("%Y-%m-%d")
        tp = self.calc_throughput(kanban_data, past, today)
        mc = self.run_simulation(tp)
        mc = mc.rename(index={'issues': kanban_data.loc[0]['project']})
        result = ct.merge(mc, left_index=True, right_index=True)
        return result

    def generate_url(self):
        url = (
            "https://aod.eazybi.com/accounts/" + str(cfg['Account_number']) +
            "/export/report/" + str(cfg['Report_number']) +
            "-api-export.csv?embed_token=" + str(cfg['Report_token']))
        return url

    def get_eazybi_report(self, report_url):
        dictio = pd.read_csv(report_url, delimiter=',', parse_dates=['Time'])
        dictio.columns = ['project', 'date', 'issue', 'cycletime']
        return dictio

    def calc_cycletime_percentile(self, kanban_data, percentile=None):
        """Calculate cycletime percentiles on cfg with all dict entries"""
        if kanban_data.empty is False:
            if percentile is not None:
                issuetype = kanban_data.groupby('project').cycletime.quantile(
                    percentile / 100).apply(np.ceil).astype('int')
                return issuetype
            else:
                cycletime = None
                for cfg_percentile in cfg['Cycletime']['Percentiles'].get():
                    temp_cycletime = kanban_data.groupby(
                        'project').cycletime.quantile(
                        cfg_percentile / 100).rename(
                        'cycletime '+str(cfg_percentile)+'%').apply(
                            np.ceil).astype('int')
                    if cycletime is None:
                        cycletime = temp_cycletime.to_frame()
                    else:
                        cycletime = cycletime.merge(
                            temp_cycletime, left_index=True, right_index=True)
                return cycletime

    def calc_throughput(self, kanban_data, start_date=None, end_date=None):
        """Change the pandas DF to a Troughput per day format, a good
        throughput table has all days from start date to end date filled
        with zeroes if there are no ocurrences

        Parameters
        ----------
            kanban_data : dataFrame
                dataFrame to be sorted by throughput (number of ocurrences
                per day)
            start_date : date
                earliest date of the throughput
            end_date : date
                final date of the throughput
        """
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
            if throughput.empty is False and (
                    start_date is not None and end_date is not None):
                date_range = pd.date_range(
                    start=start_date,
                    end=end_date
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


class Hello(Resource):
    def get(self):
        return {'message': 'All ok!'}


api.add_resource(Hello, '/')
api.add_resource(Eazybi, '/eazybi/<string:filename>')

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
    # Eazybi().get()
