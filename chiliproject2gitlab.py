#!/usr/bin/env python3
from __future__ import print_function
import requests
import csv
import sys
try:
    from settings import PRIVATE_TOKEN, API_URL, manual_mapping
except ImportError:
    print("You need to create a settings.py file with the following content:")
    print("PRIVATE_TOKEN = 'gitlab private token'")
    print("API_URL = 'gitlab api url'")
    print("manual_mapping = {'chiliprojectname1': 'gitlab name1', 'chiliproject name2': 'gitlab name2'}")
    print("\n")
    sys.exit(-1)

# get gitlab project names and ids
# get first 100 gitlab projects
gitlab_project_names = {}
r = requests.get('%s/projects?private_token=%s&per_page=100' % (API_URL, PRIVATE_TOKEN))
assert r.status_code == 200
for project in r.json():
    gitlab_project_names[project['name'].lower()] = project['id']

if len(gitlab_project_names) == 100:
    raise NotImplementedError("Gitlab API restricts page_sizes to 100. Implement successive requests to get all your projects")

# get gitlab user names and ids
r = requests.get('%s/users?private_token=%s&per_page=100' % (API_URL, PRIVATE_TOKEN))
assert r.status_code == 200
assert len(r.json()) != 100
gitlab_assignees = {}
for user in r.json():
    gitlab_assignees[user['name'].lower()] = user['id']

# read chiliproject issues.
issue_file = open('export.csv', 'r', encoding='ISO-8859-1')
# dict comprehension to copy data.
chiliproject_issues = [line for line in csv.DictReader(issue_file, delimiter=',', quotechar='"')]
issue_file.close()

# get gitlab project names. Lowercase
chiliproject_project_names = set()
for chiliproject_issue in chiliproject_issues:
    chiliproject_project_names.add(chiliproject_issue['Project'].lower())

# debug info
project_names_not_in_gitlab = chiliproject_project_names - set(gitlab_project_names)
unmapped_project_names = project_names_not_in_gitlab - set(manual_mapping)
if len(unmapped_project_names) > 0:
    raise IOError('No known mapping for chiliproject project names: ' + ' '.join(sorted(unmapped_project_names)))

# chiliproject project name to gitlab project id
project_mappings = {}
for p in chiliproject_project_names:
    # prefer manual mapping
    if p in manual_mapping:
        project_mappings[p] = gitlab_project_names[manual_mapping[p]]
    else:
        project_mappings[p] = gitlab_project_names[p]

# add issues to gitlab
for issue in chiliproject_issues:
    labels = [issue['Priority'], issue['Tracker']]

    # required
    gitlab_project_id = project_mappings[issue['Project'].lower()]
    gitlab_issue = {}
    gitlab_issue['title'] = issue['Subject']

    # optional
    if issue['Description']:
        gitlab_issue['description'] = issue['Description']

    if labels:
        gitlab_issue['labels'] = ','.join(labels)

    if issue['Assignee']: # nonempty
        gitlab_issue['assignee_id'] = gitlab_assignees[issue['Assignee'].lower()]

    # create new issue
    print('Creating new issue:', issue['Subject'])
    r = requests.post('%s/projects/%d/issues?private_token=%s' % (API_URL, gitlab_project_id, PRIVATE_TOKEN), gitlab_issue)
    assert r.status_code == 201

    # get issue id of just created issue
    # newest issues first
    r = requests.get('%s/projects/%d/issues?private_token=%s&per_page=1' % (API_URL, gitlab_project_id, PRIVATE_TOKEN))
    assert r.status_code == 200
    last_issue = r.json()[0]
    last_issue_id = last_issue['id']

    # make sure, we have the proper issue
    assert last_issue['title'] == gitlab_issue['title']
    assert last_issue['state'] == 'opened'

    # close issue
    if issue['Status'] == 'Closed':
        print('  Closing issue...')
        r = requests.put('%s/projects/%d/issues/%d?private_token=%s' % (API_URL, gitlab_project_id, last_issue_id, PRIVATE_TOKEN), {'state_event': 'close'})
        assert r.status_code == 200

    # TODO Remove me, when ready
    break