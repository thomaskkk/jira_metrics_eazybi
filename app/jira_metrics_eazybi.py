#!/usr/bin/env python

import requests

def main():
    api_url = "https://jsonplaceholder.typicode.com/todos/1"
    response = requests.get(api_url)
    print(response.json())


if __name__ == "__main__":
    main()