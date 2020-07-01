# -*- coding: utf-8 -*-
#Python 3.7
#paxata-trials.py - Setup Paxata trials
#Version: 0.1
#Date: 1st July 2020

import requests,json,random,string,urllib,boto3,logging
from urllib3.exceptions import InsecureRequestWarning
from requests.auth import HTTPBasicAuth

def randomPassword():
    randomSource = string.ascii_letters + string.digits + string.punctuation
    password = random.choice(string.ascii_lowercase)
    password += random.choice(string.ascii_uppercase)
    password += random.choice(string.digits)
    #password += random.choice(string.punctuation)
    #Paxata passwords MUST have one of the below
    password += random.choice("!@#$%^&*+=")

    for i in range(6):
        password += random.choice(randomSource)

    passwordList = list(password)
    random.SystemRandom().shuffle(passwordList)
    password = ''.join(passwordList)
    return password
def send_email_via_aws_lambda(url,recipient,password):
    # This first "IF" statement is checking if it is the FIRST dataset, if it is, then download the column headers
    post_request = ("https://ib6l2juafj.execute-api.us-west-2.amazonaws.com/default/send_email_via_ses")
    api_key = "ane0sU7BKA4hKkgCzN7Pl9jWaMbVA28p6Gu6iR3R"
    payload = {
        "SENDER": "noreply@datarobot.com",
        "RECIPIENT": recipient,
        "SUBJECT": "Paxata Trial Registration",
        "BODY_TEXT": "This email was sent to you to register you for a Paxata trial, please log in with your email address in lower case and this password" + str(password),
        "BODY_HTML": "\"<html><head></head><body><h1>Your Login details for your Paxata Trial</h1><p>This email was sent to you to register you for a Paxata trial, please log in with your email address in lower case and this password" + str(password) + "</p></body></html>\""
        }
    post_response = requests.post(post_request, auth=HTTPBasicAuth("",api_key), params=payload)
    if (post_response.ok):
        response_content = post_response.content
    else:
        response_content = "Didn't send email. Status code " + str(post_response.status_code)
    return response_content

def add_user_to_paxata(auth_token,paxata_url,username,password,tenantId):
    # This first "IF" statement is checking if it is the FIRST dataset, if it is, then download the column headers
    #post_request = (paxata_url + "/rest/users?name="+urllib.parse.quote(username, safe='')+"&email="+urllib.parse.quote(username, safe='')+"&password="+password+"&roles=PowerUser,RemoteAccess,Automation&tenantId=9c2c8225e2674fd6a20c188040033399")
    post_request = (paxata_url + "/rest/users")
    payload = {
            "name": username,
            "email": username,
            "password": password,
            "tenantId": tenantId,
            "roles": "PowerUser"
    }
    post_response = requests.post(post_request, auth=auth_token, params=payload)
    #post_response = requests.post(post_request, auth=auth_token)
    if (post_response.ok):
        function_response = "Created - User = " + username + " - Password = " + password
    else:
        if (post_response.status_code == "409"):
            function_response = "Not Created - User =" + username + " - Already exists in tenant - " + paxata_url
        else:
            function_response = "Not Created - User =" + username + " - Status code =" + str(post_response.status_code)
    return function_response


if __name__ == "__main__":
    with open('config.json', 'r') as f:
        config = json.load(f)
    #aws_lambda_variables
    lambda_location = "/tmp/"
    client = boto3.client('s3')
    s3 = boto3.resource('s3')
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)


    users_file = open("users.txt", "r")
    paxata_url = str(config["paxata-url"])
    tenantId = str(config["tenantId"])

    users_output = "users_output.txt"
    users_output_file = open(users_output, "w")
    users_output_file.close()
    users_output_file = open(users_output, "a")

    pax_auth_token = HTTPBasicAuth("",config["rest-token"])

    for user in users_file:
        username = user.rstrip()
        password = randomPassword()
        add_user_response = add_user_to_paxata(pax_auth_token,paxata_url,username,password,tenantId)
        #if add_user_response[0:6] == "Created":
        #    send_email_response = send_email_via_aws_lambda(config['paxata-url'],username,password)
        users_output_file.write(add_user_response+"\n")
        print(add_user_response)

    print ("Done")
    users_output_file.close()