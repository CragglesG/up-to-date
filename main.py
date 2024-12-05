from slack_bolt import App

app = App()

@app.command("/getmeuptodate")
def get_me_up_to_date(ack, body, client):
    ack()
    # TODO: get the user up to date on up to date!
