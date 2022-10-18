from PureCloudPlatformClientV2.rest import ApiException
import PureCloudPlatformClientV2
import websockets
import asyncio
import sys
import os
import json


print("\n-----------------------------------------------------")
print("--- Genesys Cloud Python SDK Notification Service ---")
print("-----------------------------------------------------")

print("\nYou can exit the application at anytime with Ctrl c..")

CLIENT_ID = os.environ["GC_CLIENT_ID"]
CLIENT_SECRET = os.environ["GC_CLIENT_SECRET"]
ENVIRONMENT = os.environ["GC_ENVIRONMENT"] # eg. mypurecloud.com or mypurecloud.ie


def find_queue_id(queue_name, routing_api_instance):
    try:
        # find queue id by filtering all queues by queue name
        response = routing_api_instance.get_routing_queues(name=queue_name)
        if response.entities == []:
            return
        for entity in response.entities:
            if entity.name == queue_name: 
                print("\nHurray we found your queue!\n")
                print(f"Queue name = {entity.name}")
                print(f"Queue id = {entity.id}")
                return entity.id
    except ApiException as e:
        print("Exception when calling RoutingApi->get_routing_queues: %s\n" % e)
    

def create_notifications_channel(notifications_api_instance):
    try:
        print("\nCreating notifications channel..")
        # Create the channel
        response = notifications_api_instance.post_notifications_channels()
        return response
    except ApiException as e:
        print("Exception when calling NotificationsApi->post_notifications_channels: %s\n" % e)


def subscribe_to_topic(queue_id, channel_id, notifications_api_instance):
    # the topic we want to subscribe to
    body = [
        {"id": f"v2.routing.queues.{queue_id}.users"}
    ]
    try:
        print(f"\nSubscribing to v2.routing.queues.{queue_id}.users")
         # Replace the current list of subscriptions with a new list.
        notifications_api_instance.put_notifications_channel_subscriptions(channel_id, body)
    except ApiException as e:
        print("\nException when calling NotificationsApi->post_notifications_channel_subscriptions: %s\n" % e)


async def listen(uri, queue_name):
    print("\nOpening web socket connection to notifications channel..")
    # open the websocket connection
    async with websockets.connect(uri) as websocket:
        print(f"\nConnected! You can now listen to notification events from {queue_name}")
        async for response in websocket:
            # format messages
            json_object = json.loads(response)
            json_formatted_str = json.dumps(json_object, indent=4)
            print(json_formatted_str)


def main():
    # Authenticate
    api_client = PureCloudPlatformClientV2.api_client.ApiClient().get_client_credentials_token(CLIENT_ID, CLIENT_SECRET)
    # create an instance of the API class
    notifications_api_instance = PureCloudPlatformClientV2.NotificationsApi(api_client)
    routing_api_instance = PureCloudPlatformClientV2.RoutingApi(api_client)
    queue_name = input("\nEnter the name of the queue you want to listen to: ")
    # find the queue id for the queue you want to listen to
    queue_id = find_queue_id(queue_name, routing_api_instance)
    if queue_id == None:
        print("\nQUEUE NOT FOUND..")
        sys.exit(0)
    # 1. create the notifications channel
    response = create_notifications_channel(notifications_api_instance)
    # 1.1 extract connect uri and channel id from the response
    uri = response.connect_uri
    channel_id = response.id
    # 2. subscribe to a topic 
    subscribe_to_topic(queue_id, channel_id, notifications_api_instance)
    # 3. open a web socket connection to the notifications channel
    asyncio.get_event_loop().run_until_complete(listen(uri, queue_name))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
    except RuntimeError:
        sys.exit(0)
