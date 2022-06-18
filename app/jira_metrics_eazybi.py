#!/usr/bin/env python

import requests
import csv
# from pprint import pprint


def main():
    api_url = "https://aod.eazybi.com/accounts/70597/export/report/1075725-api-export.csv?embed_token=iid25hgzq92p8km005mmfz62q3cqchs58tbeudl24wi4dd64nsrsdcnnxapi"
    with requests.Session() as s:
        download = s.get(api_url)

        decoded_content = download.content.decode('utf-8')

        cr = csv.reader(decoded_content.splitlines(), delimiter=',')
        my_list = list(cr)
        for row in my_list:
            print(row)


if __name__ == "__main__":
    main()
