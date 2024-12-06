from slack_bolt import App

app = App()

@app.command("/getmeuptodate")
def get_me_up_to_date(ack, body, client):
    ack()
    # TODO: get the user up to date on Up To Date!

@app.command("/utdpost")
def post(ack, client):
    ack()
    # TODO: Show posting modal

# TODO: Receive posting modal submission

@app.command("/utdtopic")
def topic(ack, client):
    ack()
    # TODO: Show topic modal

# TODO: Receive topic modal submission

# TODO: Implement feed posting mechanism
