# colalb_sessions
## Blackboard Collaborate session creation in a Blackboard Learn Ultra course via API

This is a simple python3 script to demonstrate how to create Collaborate sessions in Learn via the Collaborate REST API.

To make it work you need to:

* __Fill the information in the config.json template.__ You need to register a Learn application in the developer portal to get the key and secret, and   this app needs to be deployed in the Learn environment. Key and secret for collaborate are the LTI credentials for the integration user in said Learn   environment. Do not forget to remove "(template), name should be "config.json"
* __Install dependencies from requirements.txt file__, using either pip install -r requirements.txt or pip3 install -r requirements.txt
* __Run sessions.py__ and folow on screen instructions
