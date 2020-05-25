import cv2
import datetime
import numpy as np
from cloudant.client import Cloudant
from cloudant.error import CloudantException
from cloudant.result import Result, ResultByKey

import ibm_boto3
from ibm_botocore.client import Config, ClientError
import time

#Provide CloudantDB credentials such as username,password and url
client = Cloudant("8f03c090-ff65-4bfb-8ff7-7bb3f526fd5b-bluemix", "9f35def67e3f66d942b35c52ce21e86c1396e081a735578e228a9b509f7297d6", url="https://8f03c090-ff65-4bfb-8ff7-7bb3f526fd5b-bluemix:9f35def67e3f66d942b35c52ce21e86c1396e081a735578e228a9b509f7297d6@8f03c090-ff65-4bfb-8ff7-7bb3f526fd5b-bluemix.cloudantnosqldb.appdomain.cloud")
client.connect()

#Provide your database name
database_name = "project2"
my_database = client.create_database(database_name)

if my_database.exists():
   print(f"'{database_name}' successfully created.")
  

img=cv2.VideoCapture(0)

while True:
       ret,frame=img.read()
       
       global imgname

       cv2.imshow("Employee_Face",frame)
       imgname=datetime.datetime.now().strftime("%y-%m-%d-%H-%M-%S")
       cv2.imwrite(imgname+".jpg",frame)
       k=cv2.waitKey(1)
       #waitKey(1)- for every 1 millisecond new frame will be captured
       if k==ord('q'):
        #release the camera
                img.release()
        #destroy all windows
                cv2.destroyAllWindows()
                break

# Constants for IBM COS values
COS_ENDPOINT = "https://s3.jp-tok.cloud-object-storage.appdomain.cloud" # Current list avaiable at https://control.cloud-object-storage.cloud.ibm.com/v2/endpoints
COS_API_KEY_ID = "P7vluJ26j6F1Li1_6ddLIZ8K15kHHrJcaMj5cD75Iy_-" # eg "W00YiRnLW4a3fTjMB-odB-2ySfTrFBIQQWanc--P3byk"
COS_AUTH_ENDPOINT = "https://iam.cloud.ibm.com/identity/token"
COS_RESOURCE_CRN = "crn:v1:bluemix:public:cloud-object-storage:global:a/58ac0db086aa48898bdfffdd48180291:45fcb933-75ac-4cc7-a7c9-244767458ba2::"

# Create resource
cos = ibm_boto3.resource("s3",
    ibm_api_key_id=COS_API_KEY_ID,
    ibm_service_instance_id=COS_RESOURCE_CRN,
    ibm_auth_endpoint=COS_AUTH_ENDPOINT,
    config=Config(signature_version="oauth"),
    endpoint_url=COS_ENDPOINT
)

def create_bucket(bucket_name):
    print("Creating new bucket: {0}".format(bucket_name))
    try:
        cos.Bucket(bucket_name).create(
            CreateBucketConfiguration={
                "LocationConstraint":"jp-tok-standard"
            }
        )
        print("Bucket: {0} created!".format(bucket_name))
    except ClientError as be:
        print("CLIENT ERROR: {0}\n".format(be))
    except Exception as e:
        print("Unable to create bucket: {0}".format(e))

create_bucket("ibk")

def multi_part_upload(bucket_name, item_name, file_path):
        try:
            print("Starting file transfer for {0} to bucket: {1}\n".format(item_name, bucket_name))

            # set 5 MB chunks
            part_size = 1024 * 1024 * 5

            # set threadhold to 15 MB
            file_threshold = 1024 * 1024 * 15

            # set the transfer threshold and chunk size
            transfer_config = ibm_boto3.s3.transfer.TransferConfig(
                multipart_threshold=file_threshold,
                multipart_chunksize=part_size
            )
            # the upload_fileobj method will automatically execute a multi-part upload
            # in 5 MB chunks for all files over 15 MB
            with open(file_path, "rb") as file_data:
                cos.Object(bucket_name, item_name).upload_fileobj(
                    Fileobj=file_data,
                    Config=transfer_config
                )

            print("Transfer for {0} Complete!\n".format(item_name))
        except ClientError as be:
            print("CLIENT ERROR: {0}\n".format(be))
        except Exception as e:
            print("Unable to complete multi-part upload: {0}".format(e))
multi_part_upload("ibk", "image.jpg", imgname+".jpg")
json_document={"link":COS_ENDPOINT+"/"+"ibk"+"/"+"image.jpg"}
new_document = my_database.create_document(json_document)

import json
from watson_developer_cloud import VisualRecognitionV3

visual_recognition = VisualRecognitionV3(
    '2018-03-19',
    iam_apikey="0MmNQwIZEKyukQygp1lp312e7R0yFdZRHaqqntiOvVGo")

with open(imgname+'.jpg', 'rb') as images_file:
    classes1 = visual_recognition.classify(
        images_file,
        threshold='0.6',
	classifier_ids='Default_567702618').get_result()
'print(type(classes1))'
print(json.dumps(classes1, indent=2))
print(classes1["images"][0]["classifiers"][0]["classes"][0])
a=classes1["images"][0]["classifiers"][0]["classes"][0]["class"]

from ibm_watson import TextToSpeechV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from playsound import playsound

authenticator = IAMAuthenticator("iwnspiBaK117WrVP5eTCljivlC2brGwYg_PKEt1MlVFP")
text_to_speech = TextToSpeechV1(
    authenticator=authenticator
)

text_to_speech.set_service_url("https://api.eu-gb.text-to-speech.watson.cloud.ibm.com/instances/b0fb2355-1377-4242-9015-fccdd17051d8")

with open('project.mp3', 'wb') as audio_file:
        if(a=="Wearing helmet"):
                audio_file.write(
                        text_to_speech.synthesize(
                                f'Employee is {a} and allow inside',
                                voice='en-US_AllisonVoice',
                                accept='audio/mp3'
                                ).get_result().content)

        else:
                audio_file.write(
                        text_to_speech.synthesize(
                                f'Employee is {a} and do not allow inside',
                                voice='en-US_AllisonVoice',
                                accept='audio/mp3'
                                ).get_result().content)
                import requests
                r = requests.get('https://www.fast2sms.com/dev/bulk?authorization=XrBTQsmZxWGqYn98k5SK0J17zRcufvyE4HeVgPl62hMNdAwj3ob3TEDtGJXY6I4gBAcRxpusyPovONZ1&sender_id=FSTSMS&message=Employee is not wearing helmet&language=english&route=p&numbers=9676847472')


playsound('project.mp3')



