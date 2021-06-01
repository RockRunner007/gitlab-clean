#!/bin/python3

import json
import requests
import logging
from datetime import datetime, timedelta

def configure_logging():
    logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

def _set_headers(username: str = None, api_key: str = None):
    headers = {'Content-Type': 'application/json'}
    if username: headers['Authorization'] = f'Basic {username}'
    if api_key: headers['PRIVATE-TOKEN'] = f'{api_key}'
    return headers

def _set_uri():
    return '{gitlab}/api/v4'

def get_access_token():
    return ''

def process_api_request(url: str, verb: str, headers: dict, data: dict = None, params: dict = None):
    try:
        if data: r = getattr(requests, verb.lower())(url,headers=headers,data=json.dumps(data))
        elif params: r = getattr(requests, verb.lower())(url,headers=headers,params=params)
        else: r = getattr(requests, verb.lower())(url,headers=headers)

        r.raise_for_status()
    except Exception as e:
        logging.error(f'An error occured executing the API call: {e}')

    try:
        return r.json()
    except Exception as e:
        logging.error(f'An error occured loading the content: {e}')
        return None

def get_jobs(token, page, project_id):
    data = {
        'page' : page,
        'per_page' : 50
    }
    # List project jobs | https://docs.gitlab.com/ee/api/jobs.html#list-project-jobs
    return process_api_request(f'https://{_set_uri()}/projects/{project_id}/jobs', 'GET', _set_headers(api_key=token), params=data)

def get_job_count(token, page, project_id):
    count = get_jobs(token, page, project_id)
    if len(count) > 0: return True
    return False

def delete_artifacts(token, project_id, job_id):
    # Delete job artifacts | https://docs.gitlab.com/ee/api/job_artifacts.html#delete-artifacts
    try:
        process_api_request(f'https://{_set_uri()}/projects/{project_id}/jobs/{job_id}/artifacts', 'DELETE', _set_headers(api_key=token))
    except Exception as e:
        logging.error(f'An error occured loading the content: {e}')
    return False

def main():
    configure_logging()
    token=get_access_token()
    project_id='254'
    
    logging.info(f"Start cleaning project: {project_id}")

    page_count = 1
    while get_job_count(token, page_count, project_id):
        jobs = get_jobs(token, page_count, project_id)
            
        for entry in jobs:
            create_date = datetime.strptime(entry["created_at"], '%Y-%m-%dT%H:%M:%S.%fZ')
            time_between_insertion = datetime.now() - create_date

            if time_between_insertion.days>=30 and len(entry["artifacts"]) > 0:
                #logging.info(f"Remove job artifacts for job {entry['id']}")
                delete_artifacts(token,project_id,entry["id"])                
        page_count +=1

    logging.info(f"Finished cleaning project {project_id}")

if __name__ == "__main__":
    main()