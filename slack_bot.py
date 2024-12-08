"""Up To Date Slack bot."""

import os
import json
import dotenv
import uvicorn
from requests import patch
from slack_bolt import App
from slack_bolt.adapter.asgi.builtin import SlackRequestHandler
from appwrite.client import Client
from appwrite.services.databases import Databases
from utils import (
    clean_string,
    add_or_update_user,
    add_or_update_post,
    get_topics,
    EnumUpdateFailed,
)


dotenv.load_dotenv()

app = App(
    token=os.getenv("SLACK_BOT_TOKEN"), signing_secret=os.getenv("SLACK_SIGNING_SECRET")
)

api = SlackRequestHandler(app)

db_client = Client()
db_client.set_endpoint("https://cloud.appwrite.io/v1")
db_client.set_project("up-to-date-slack-bot")
db_client.set_key(os.getenv("APPWRITE_API_KEY"))

databases = Databases(db_client)


@app.command("/getmeuptodate")
def get_me_up_to_date(ack, body, client):
    """Set up the user with Up To Date."""
    ack()
    with open("views/getmeuptodate.json", encoding="utf-8") as f:
        view = json.load(f)
    client.chat_postEphemeral(
        channel=body["channel_id"],
        user=body["user_id"],
        text="Welcome to Up To Date! This message usually renders using blocks, \
        which doesn't appear to have worked. Maybe try again soon?",
        blocks=view["blocks"],
    )


@app.action("signup-topics-action")
def signup_topics_action(ack, body):
    """Handle the user's topic selection."""
    ack()
    add_or_update_user(
        databases,
        body["user"]["id"],
        data={
            "user-id": body["user"]["id"],
            "topics": [
                entry["value"] for entry in body["actions"][0]["selected_options"]
            ],
        },
    )


@app.action("signup-channels-action")
def signup_channels_action(ack, body):
    """Handle the user's channel selection."""
    ack()
    add_or_update_user(
        databases,
        body["user"]["id"],
        {"channels": body["actions"][0]["selected_conversations"]},
    )


@app.command("/utdpost")
def post(ack, body, client):
    """Open the post modal."""
    ack()
    with open("views/post.json", encoding="utf-8") as f:
        view = json.load(f)

    client.views_open(trigger_id=body["trigger_id"], view=view)


@app.options("post-topics-action")
@app.options("signup-topics-action")
def topics_options(ack):
    """Handle the post/setup topics options."""
    topics = get_topics(databases)
    options = [
        {
            "text": {"type": "plain_text", "text": name, "emoji": True},
            "value": id,
        }
        for name, id in zip(topics["topic-names"], topics["topic-ids"])
    ]
    ack(options=options)


@app.view_submission("post-modal")
def post_modal_submission(ack, body, client):
    """Handle the post modal submission."""
    ack()
    title: str = body["view"]["state"]["values"][body["view"]["blocks"][1]["block_id"]][
        "post-title-action"
    ]["value"]
    title_cleaned: str = clean_string(title)
    content: str = body["view"]["state"]["values"][
        body["view"]["blocks"][2]["block_id"]
    ]["post-content-action"]["rich_text_value"]["elements"][0]
    topics = body["view"]["state"]["values"][body["view"]["blocks"][3]["block_id"]][
        "post-topics-action"
    ]["selected_options"]
    channels = body["view"]["state"]["values"][body["view"]["blocks"][4]["block_id"]][
        "post-channels-action"
    ]["selected_conversations"]

    with open(f"posts/{title_cleaned}.md", "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n{str(content)}")

    add_or_update_post(
        databases,
        title_cleaned,
        data={
            "post-link": f"https://utd-posts.craigg.hackclub.app/{title_cleaned}.md",
            "topics": [topic["value"] for topic in topics],
            "channels": channels,
        },
    )

    for channel in channels:
        client.chat_postMessage(
            channel=channel,
            text=f"A new Up To Date post has been attributed to this channel.\n Title: {title}",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"A new Up To Date post has been \
attributed to this channel\n Title: {title}\n\n",
                    },
                },
                {"type": "rich_text", "elements": [content]},
            ],
        )

    response = databases.list_documents("topics-and-channels", "ts-and-cs-data")
    users = response.get("documents", [])
    for user in users:
        if any(topic["value"] in user["topics"] for topic in topics):
            client.chat_postMessage(
                channel=user["user-id"],
                text=f"New post with one of your topics.\nTitle: {title} \
(Content could not render properly. Contact <@U07FBU5MM8U|Craig> for help.)",
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"New post with one of your topics\nTitle: {title}\n\n",
                        },
                    },
                    {"type": "rich_text", "elements": [content]},
                ],
            )
        if any(channel in user["channels"] for channel in channels):
            client.chat_postMessage(
                channel=user["user-id"],
                text=f"New post with one of your channels.\nTitle: {title} \
(Content could not render properly. Contact <@U07FBU5MM8U|Craig> for help.)",
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"New post with one of your channels.\nTitle: {title}\n\n",
                        },
                    },
                    {"type": "rich_text", "elements": [content]},
                ],
            )


@app.command("/utdtopic")
def topic(ack, body, client):
    """Open the topic modal."""
    ack()
    with open("views/topic.json", encoding="utf-8") as f:
        view = json.load(f)
    client.views_open(trigger_id=body["trigger_id"], view=view)


@app.view_submission("topic-modal")
def topic_modal_submission(ack, body, client):
    """Handle the topic modal submission."""
    ack()
    topic_name: str = body["view"]["state"]["values"][
        body["view"]["blocks"][1]["block_id"]
    ]["topic-name-action"]["value"]
    topic_id: str = body["view"]["state"]["values"][
        body["view"]["blocks"][2]["block_id"]
    ]["topic-id-action"]["value"]

    databases.create_document(
        "topics-and-channels",
        "all-topics",
        clean_string(topic_id),
        {"topic-name": topic_name, "topic-id": topic_id},
    )

    topic_ids = get_topics(databases)["topic-ids"]

    r1 = patch(
        "https://cloud.appwrite.io/v1/databases/\
topics-and-channels/collections/ts-and-cs-data/attributes/enum/topics",
        headers={
            "content-type": "application/json",
            "X-Appwrite-Project": "up-to-date-slack-bot",
            "X-Appwrite-Key": os.getenv("APPWRITE_API_KEY"),
        },
        data=json.dumps(
            {
                "required": False,
                "elements": topic_ids,
                "default": None,
            }
        ),
        timeout=30,
    )

    r2 = patch(
        "https://cloud.appwrite.io/v1/databases/\
utd-posts/collections/posts-data/attributes/enum/topics",
        headers={
            "content-type": "application/json",
            "X-Appwrite-Project": "up-to-date-slack-bot",
            "X-Appwrite-Key": os.getenv("APPWRITE_API_KEY"),
        },
        data=json.dumps(
            {
                "required": False,
                "elements": topic_ids,
                "default": None,
            }
        ),
        timeout=30,
    )
    if r2.status_code != 200 or r1.status_code != 200:
        print(r1.json())
        print(r2.json())
        client.chat_postMessage(
            channel=body["user"]["id"],
            text="Failed to update enum fields.",
        )
        raise EnumUpdateFailed("Failed to update enum fields.")

    client.chat_postMessage(
        channel=body["user"]["id"],
        text=f"Topic {topic_name} has been added successfully.",
    )


if __name__ == "__main__":
    uvicorn.run(api, host="0.0.0.0", port=int(os.getenv("PORT", "3000")))
