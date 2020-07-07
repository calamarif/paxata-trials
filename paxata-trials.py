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

def post_message_to_slack(message):
    slack_url = "https://hooks.slack.com/services/"
    slack_unique_id = "T3Z1R3DNG/B0171KPC6KA/kxgeUrqwnCEO90fibpL5jr6C"
    slack_message = '{"text": \"'+ message +'\"}'

    slack_request = slack_url + slack_unique_id
    try:
        slack_post_msg_response = requests.post(slack_request, verify=False, data=slack_message)
    except:
        print ("DEBUG: Posting message failed")

def s3_bucket_upload(s3, bucket_name,file_name):
    # Upload the file to S3
    #s3.meta.client.upload_file("/tmp/"+file_name, bucket_name, file_name)
    s3.meta.client.upload_file(file_name, bucket_name, file_name)
    
def s3_bucket_download (client, bucket_name,file_name):
    # Download the file from S3
    client.download_file(bucket_name, file_name, "/tmp/"+file_name)


if __name__ == "__main__":
    with open('config.json', 'r') as f:
        config = json.load(f)
    #aws_lambda_variables
    lambda_location = "/tmp/"
    client = boto3.client('s3')
    s3 = boto3.resource('s3')
    bucket_name = "paxata-trial-app"

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    with open('users.json', 'r') as uf:
        users_file = json.load(uf)
    #users_file = open("users.txt", "r")

    paxata_url = str(config["paxata-url"])
    tenantId = str(config["tenantId"])

    users_output = "users_output.txt"
    users_output_file = open(users_output, "w")
    users_output_file.close()
    users_output_file = open(users_output, "a")

    pax_auth_token = HTTPBasicAuth("",config["rest-token"])

    #3. Process File
    for user in users_file:
        username = users_file[user]
        password = randomPassword()
        add_user_response = add_user_to_paxata(pax_auth_token,paxata_url,username,password,tenantId)
        #if add_user_response[0:6] == "Created":
        #    send_email_response = send_email_via_aws_lambda(config['paxata-url'],username,password)
        users_output_file.write(add_user_response+"\n")
        post_message_to_slack(add_user_response)

    logger.info(users_output+' has been written')
    users_output_file.close()
    s3_bucket_upload(s3, bucket_name, users_output_file)
