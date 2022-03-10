# bbb-bot

This is a test project to create load on BigBlueButton server. 

## Usage
Authentication is done via [RCP](https://github.com/myOmikron/rcp). The endpoint name is used as salt. 
Body data is encoded with json.

### `/api/v1/startBot`
- Method: `POST`

**Parameter**:

| Name           | Type | Description                                    |
|----------------|------|------------------------------------------------|
| sender         | bool | Specify True, if the bot should send audio     |
| meeting_id     | str  | Meeting ID of a running BigBlueButton meeting  |
| bbb_server_uri | str  | Uri of the BBB Server (`bbb-conf --secret`)    |
| bbb_secret     | str  | Secret of the BBB Server (`bbb-conf --secret`) |


### `/api/v1/stopAllBots`
- Method: `POST`

No parameters are required.