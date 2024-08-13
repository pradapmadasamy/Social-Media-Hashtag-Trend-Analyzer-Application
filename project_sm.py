#Streamlit Application

import streamlit as st
import boto3
import json

# AWS setup - replace with your actual keys
AWS_ACCESS_KEY_ID = "AKIAYS2NUYT4FLWRS3DT"
AWS_SECRET_ACCESS_KEY = "V7s15D26sU+sdnC4PyvAL0fqkkgqUSdRxDul2rHJ"
AWS_REGION_NAME = "ap-southeast-2"

# Boto3 clients
dynamodb = boto3.resource('dynamodb', aws_access_key_id=AWS_ACCESS_KEY_ID,aws_secret_access_key=AWS_SECRET_ACCESS_KEY,region_name=AWS_REGION_NAME)

lambda_client = boto3.client('lambda',aws_access_key_id=AWS_ACCESS_KEY_ID,aws_secret_access_key=AWS_SECRET_ACCESS_KEY,region_name=AWS_REGION_NAME)

# Streamlit app
st.title("Social Media Hashtag Trend Analyzer Application")

post_text = st.text_area("Compose your post", max_chars=280)
hashtags = st.text_input("#Hashtags")

if st.button("Publish Post and Show Trending Hashtag"):
    if post_text and hashtags:
        # Create payload for Lambda function
        payload = {
            "post_text": post_text,
            "hashtags": hashtags.split(",")
        }

        # Invoke Lambda function to process the post
        response = lambda_client.invoke(
            FunctionName='posthashtag',
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )

        response_payload = json.loads(response['Payload'].read())
        st.success("Post published successfully!")

        # Display trending hashtags
        st.subheader("Trending Hashtags")
        trending_hashtags = response_payload.get('trending_hashtags', [])
        for hashtag in trending_hashtags:
            st.write(f"#{hashtag}")
    else:
        st.error("Please fill out both the post and hashtags fields.")


#Lambda Function

import json
import boto3
from collections import Counter

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('socialmedia')

def lambda_handler(event, context):
    # Get post_text and hashtags from the event
    post_text = event.get('post_text','Default text')
    hashtags = event.get('hashtags', [])

    if not post_text:
        return {
            'statusCode': 400,
            'error': 'post_text is missing in the event'
        }

    # Store the post in DynamoDB
    table.put_item(
        Item={
            'post_id': context.aws_request_id,
            'post_text': post_text,
            'hashtags': hashtags
        }
    )

    # Fetch all posts to analyze trending hashtags
    response = table.scan()
    items = response['Items']
    all_hashtags = [hashtag for item in items for hashtag in item.get('hashtags', [])]

    # Calculate trending hashtags
    hashtag_counts = Counter(all_hashtags)
    trending_hashtags = [hashtag for hashtag, count in hashtag_counts.most_common(5)]

    return {
        'statusCode': 200,
        'trending_hashtags': trending_hashtags
    }
