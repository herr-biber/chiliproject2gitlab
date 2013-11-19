import json

pattern_notes = 'UPDATE  `gitlab`.`notes` \
SET `created_at` = \'%s\', `updated_at` = \'%s\' \
WHERE `noteable_id` = %d \
AND `note` = \'_Status changed to closed_\' \
AND `noteable_type` = \'Issue\';'

pattern_issues = 'UPDATE  `gitlab`.`issues` \
SET `created_at` = \'%s\', `updated_at` = \'%s\' \
WHERE  `issues`.`id` = %d;'

with open('new_issue_timestamps.json') as fd:
    ids = json.load(fd)

for id, timestamps in ids.items():
    print(pattern_issues % (timestamps['created'], timestamps['updated'], int(id)))

for id, timestamps in ids.items():
    print(pattern_notes % (timestamps['updated'], timestamps['updated'], int(id)))
