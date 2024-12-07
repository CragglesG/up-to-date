from slack_bolt import App
from appwrite.client import Client
from appwrite.services.databases import Databases
from utils import clean_string, add_or_update_user, add_or_update_post
import json
import dotenv
import os

dotenv.load_dotenv()

app = App(token=os.getenv("SLACK_BOT_TOKEN"), signing_secret=os.getenv("SLACK_SIGNING_SECRET"))

client = Client()
client.set_endpoint('https://cloud.appwrite.io/v1')
client.set_project('up-to-date-slack-bot')
client.set_key(os.getenv("APPWRITE_API_KEY"))

databases = Databases(client)
    
@app.command("/getmeuptodate")
def get_me_up_to_date(ack, body, client):
    ack()
    with open("views/getmeuptodate.json") as f:
        view = json.load(f)
    client.chat_postEphemeral(channel=body["channel_id"], user=body["user_id"], text="Welcome to Up To Date! This message usually renders using blocks, which doesn't appear to have worked. Maybe try again soon?", blocks=view["blocks"])

@app.action("signup-topics-action")
def signup_topics_action(ack, body, client):
    ack()
    add_or_update_user(databases, body["user"]["id"], data={"user-id": body["user"]["id"], "topics": [entry['value'] for entry in body["actions"][0]["selected_options"]]})

@app.action("signup-channels-action")
def signup_channels_action(ack, body, client):
    ack()
    add_or_update_user(databases, body["user"]["id"], {"channels": body["actions"][0]["selected_conversations"]})


@app.command("/utdpost")
def post(ack, body, client):
    ack()
    with open("views/post.json") as f:
        view = json.load(f)
    client.views_open(trigger_id=body["trigger_id"], view=view)

@app.view_submission("post-modal")
def post_modal_submission(ack, body, client):
    ack()
    title: str = body["view"]["state"]["values"][body["view"]["blocks"][1]["block_id"]]["post-title-action"]["value"]
    title_cleaned: str = clean_string(title)
    content: str = body["view"]["state"]["values"][body["view"]["blocks"][2]["block_id"]]["post-content-action"]["rich_text_value"]["elements"][0]
    topics = body["view"]["state"]["values"][body["view"]["blocks"][3]["block_id"]]["post-topics-action"]["selected_options"]
    channels = body["view"]["state"]["values"][body["view"]["blocks"][4]["block_id"]]["post-channels-action"]["selected_conversations"]

    with open(f"posts/{title_cleaned}.md", "w") as f:
        f.write(f"# {title}\n\n{str(content)}")

    add_or_update_post(databases, title_cleaned, data={"post-link": f"https://utd-posts.craigg.hackclub.app/{title_cleaned}.md", "topics": [topic["value"] for topic in topics], "channels": channels})

    for channel in channels:
        # TODO: Implement rich text parsing
        client.chat_postMessage(channel=channel, text=f"A new Up To Date post has been attributed to this channel.\n Title: {title}", blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": f"A new Up To Date post has been attributed to this channel\n Title: {title}\n\n"}}, {"type": "rich_text", "elements": [content]}])

@app.command("/utdtopic")
def topic(ack, client):
    ack()
    # TODO: Show topic modal

# TODO: Receive topic modal submission

# TODO: Implement feed posting mechanism

if __name__ == "__main__":
    app.start(3000)