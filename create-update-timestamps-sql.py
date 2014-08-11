
import json

pattern_notes = 'UPDATE  `gitlab`.`notes` \
SET `created_at` = \'%s\', `updated_at` = \'%s\' \
WHERE `noteable_id` = %d \
AND `note` = \'_Status changed to closed_\' \
AND `noteable_type` = \'Issue\';'

pattern_issues = 'UPDATE  `gitlab`.`issues` \
SET `created_at` = \'%s\', `updated_at` = \'%s\' \
WHERE  `issues`.`id` = %d;'

pattern_events_create_issue = 'UPDATE  `gitlab`.`events` \
SET `created_at` = \'%s\', `updated_at` = \'%s\' \
WHERE `events`.`target_id` = %d \
AND `target_type` = \'Issue\' \
AND `action` = 1;'

pattern_events_close_issue = 'UPDATE  `gitlab`.`events` \
SET  `created_at` =  \'%s\', `updated_at` = \'%s\' \
WHERE `events`.`target_id` = %d \
AND `target_type` = \'Issue\' \
AND `action` = 3;'

pattern_taggings = 'UPDATE `gitlab`.`taggings` \
SET `created_at` = \'%s\' \
WHERE `taggable_id` = %d \
AND `taggable_type` = \'Issue\';'

with open('new_issue_timestamps.json') as fd:
    ids = json.load(fd)

for id, timestamps in ids.items():
    print(pattern_issues % (timestamps['created'], timestamps['updated'], int(id)))

for id, timestamps in ids.items():
    print(pattern_notes % (timestamps['updated'], timestamps['updated'], int(id)))

for id, timestamps in ids.items():
    print(pattern_events_create_issue % (timestamps['created'], timestamps['created'], int(id)))
    print(pattern_events_close_issue  % (timestamps['updated'], timestamps['updated'], int(id)))

for id, timestamps in ids.items():
    print(pattern_taggings % (timestamps['created'], int(id)))