#!/usr/bin/env python3
from __future__ import print_function
import requests
import csv
import sys
import json

try:
    from settings import PRIVATE_TOKENS, API_URL, manual_mapping
except ImportError:
    print("You need to create a settings.py file with the following content:")
    print("PRIVATE_TOKENS = {'lowercase name': 'gitlab private token'")
    print("API_URL = 'gitlab api url'")
    print("manual_mapping = {'chiliprojectname1': 'gitlab name1', 'chiliproject name2': 'gitlab name2'}")
    print("\n")
    sys.exit(-1)

class GitlabWrapper:

    def __init__(self, api_url, private_tokens):
        self._api_url = api_url
        self._private_tokens = private_tokens
        self._private_token_for_reading = private_tokens['markus roth']

        # get gitlab project names and ids
        # get first 100 gitlab projects
        r = requests.get('%s/projects?private_token=%s&per_page=100' % (self._api_url, self._private_token_for_reading))
        assert r.status_code == 200

        self._project_ids = {}
        for project in r.json():
            self._project_ids[project['name'].lower()] = project['id']

        if len(self._project_ids) == 100:
            raise NotImplementedError("Gitlab API restricts page_sizes to 100. Implement successive requests to get all your projects")

        # get user names and ids
        r = requests.get('%s/users?private_token=%s&per_page=100' % (self._api_url, self._private_token_for_reading))
        assert r.status_code == 200
        assert len(r.json()) != 100
        self._user_ids = {}
        for user in r.json():
            self._user_ids[user['name'].lower()] = user['id']

    def get_project_id(self, project_name):
        return self._project_ids[project_name]

    def get_project_names(self):
        return self._project_ids.keys()

    def get_user_id(self, user_name):
        return self._user_ids[user_name]

    def get_user_names(self):
        return self._user_ids.keys()

    def add_issue(self, project_id, issue, author):
        # create new issue
        print('Creating new issue:', issue['title'])
        r = requests.post('%s/projects/%d/issues?private_token=%s' % (self._api_url, project_id, self._private_tokens[author]), issue)
        assert r.status_code == 201
        return r.json()

    def close_issue(self, project_id, issue_id, author):
        print('  Closing issue...')
        r = requests.put('%s/projects/%d/issues/%d?private_token=%s' % (self._api_url, project_id, issue_id, self._private_tokens[author]), {'state_event': 'close'})
        assert r.status_code == 200


# read chiliproject issues.
issue_file = open('export.csv', 'r', encoding='ISO-8859-1')
# dict comprehension to copy data.
chiliproject_issues = [line for line in csv.DictReader(issue_file, delimiter=',', quotechar='"')]
issue_file.close()

# get chiliproject project names. Lowercase
chiliproject_project_names = set()
for chiliproject_issue in chiliproject_issues:
    chiliproject_project_names.add(chiliproject_issue['Project'].lower())

# gitlab wrapper
gitlab = GitlabWrapper(API_URL, PRIVATE_TOKENS)

# debug info
project_names_not_in_gitlab = chiliproject_project_names - gitlab.get_project_names()
unmapped_project_names = project_names_not_in_gitlab - set(manual_mapping)
if len(unmapped_project_names) > 0:
    raise IOError('No known mapping for chiliproject project names: ' + ' '.join(sorted(unmapped_project_names)))

# chiliproject project name to gitlab project id
project_mappings = {}
for p in chiliproject_project_names:
    # prefer manual mapping
    if p in manual_mapping:
        project_mappings[p] = gitlab.get_project_id(manual_mapping[p])
    else:
        project_mappings[p] = gitlab.get_project_id(p)

# check authors in private_tokens
for issue in chiliproject_issues:
    author = issue['Author'].lower()
    if author not in PRIVATE_TOKENS:
        raise KeyError('Author "%s" not found in PRIVATE_TOKENS' % author)

gitlab_new_issue_timestamps = {}

# add issues to gitlab
for issue in chiliproject_issues:
    author = issue['Author'].lower()
    print('Adding issue "%s" by "%s"' % (issue['Subject'], author))

    labels = []
    labels.append('Priority ' + issue['Priority'])
    labels.append('Type ' + issue['Tracker'])
    labels.append(issue['Category'])
    labels.append('Chiliproject')

    # required
    gitlab_project_id = project_mappings[issue['Project'].lower()]
    gitlab_issue = {}
    gitlab_issue['title'] = issue['Subject']

    # description
    gitlab_issue['description'] = issue['Description']
    gitlab_issue['description'] += '\n\n'
    for k in ('#', 'Created', 'Updated', 'Due date', '% Done'):
        if issue[k]:
            gitlab_issue['description'] += '%s: %s\n' % (k, issue[k])

    if labels:
        gitlab_issue['labels'] = ','.join(labels)

    if issue['Assignee']:  # nonempty
        gitlab_issue['assignee_id'] = gitlab.get_user_id(issue['Assignee'].lower())

    last_issue = gitlab.add_issue(gitlab_project_id, gitlab_issue, author)

    gitlab_new_issue_timestamps[last_issue['id']] = {
        'created': issue['Created'],
        'updated': issue['Updated']
    }

    # close issue
    if issue['Status'] == 'Closed':
        gitlab.close_issue(gitlab_project_id, last_issue['id'], author)

    # TODO Remove me, when ready
    break


# TODO convert to format 2013-11-19T12:25:15Z
with open('new_issue_timestamps.json', 'w') as fd:
    json.dump(gitlab_new_issue_timestamps, fd, indent=4, sort_keys=True)