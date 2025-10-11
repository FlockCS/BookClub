import os
import boto3 # type: ignore
import json

events = boto3.client("events")

lambda_arn = os.environ["REMINDER_LAMBDA_ARN"]

def schedule_reminder(event_id, guild_id, reminder_time, reminder_type):
    rule_name = f"BookClubReminder_{event_id}_{reminder_type}"
    schedule_expression = reminder_time.strftime("cron(%M %H %d %m ? %Y)")

    events.put_rule(
        Name=rule_name,
        ScheduleExpression=schedule_expression,
        State="ENABLED",
        Description=f"Book club reminder ({reminder_type}) for event {event_id}"
    )

    events.put_targets(
        Rule=rule_name,
        Targets=[
            {
                "Id": "1",
                "Arn": lambda_arn,
                "Input": json.dumps({
                    "event_id": event_id,
                    "guild_id": guild_id,
                    "reminder_type": reminder_type
                })
            }
        ]
    )
