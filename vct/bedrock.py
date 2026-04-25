from flask import Flask, request, jsonify
from flask_cors import CORS 
import boto3
import botocore
import json

app = Flask(__name__)
CORS(app)

# Configure Bedrock Client
bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')

def read_csv_file(csv_file_path):
    try:
        with open(csv_file_path, mode='r') as csv_file:
            csv_reader = csv.reader(csv_file)
            csv_content = []
            for row in csv_reader:
                csv_content.append(", ".join(row))  # Join row values with a comma
            return "\n".join(csv_content)  # Join all rows with a newline
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return ""

@app.route('/send-to-bedrock', methods=['POST'])
def send_to_bedrock():
    user_message = request.json.get('message')
    # return jsonify({'modelResponse': user_message})
    modelId = "amazon.titan-tg1-large"
    accept = "application/json"
    contentType = "application/json"
    outputText = "\n"
    csv_content = read_csv_file('/Users/Ruhan/Desktop/val/match_results.csv')
    prompt = f"""\nCSV Data:\n{csv_content}\n\nYou are a digital assistant designed to help a VCT analyst on the following topics and related questions about building a Valorant team for VCT.
    LLM-Powered Digital Assistant Requirements

    The digital assistant should be able to provide team compositions based on provided prompts.
    
    For each team composition:
    Answer questions about player performance with specific agents (in-game playable characters)
    Assign roles to players on the team and explain their contribution
    Offensive vs. defensive roles
    Category of in-game playable character / agent (duelist, sentinel, controller, initiator)
    Assign a team IGL (team leader, primary strategist and shotcaller)
    Provide insights on team strategy and hypothesize team strengths and weaknesses
    Valorant is a team-based first-person tactical hero shooter set in the near future.[4][5][6][7] Players play as one of a set of Agents, characters based on several countries and cultures around the world.[7] In the main game mode, players are assigned to either the attacking or defending team with each team having five players on it. Agents have unique abilities, each requiring charges, as well as a unique ultimate ability that requires charging through kills, deaths, orbs, or objectives. Every player starts each round with a "classic" pistol and one or more "signature ability" charges.[5] Other weapons and ability charges can be purchased using an in-game economic system that awards money based on the outcome of the previous round, any kills the player is responsible for, and any objectives completed. The game has an assortment of weapons including secondary guns like sidearms and primary guns like submachine guns, shotguns, machine guns, assault rifles and sniper rifles.[8][9] There are automatic and semi-automatic weapons that each have a unique shooting pattern that has to be controlled by the player to be able to shoot accurately.[9] It currently offers 24 agents to choose from.
    Please answer the following question only:\n{user_message}
    """
    body = json.dumps(
        {
            "inputText": prompt,
            "textGenerationConfig": {"topP": 0.95, "temperature": 0.1},
        }
    )
    try:
        response = bedrock_client.invoke_model(
            body=body, modelId=modelId, accept=accept, contentType=contentType
        )
        response_body = json.loads(response.get("body").read())
        outputText = response_body.get("results")[0].get("outputText")
    except botocore.exceptions.ClientError as error:
        print(f"Error occurred: {error}")
        outputText = "Error occurred while invoking the model."

    return jsonify({'modelResponse': outputText})

if __name__ == '__main__':
    app.run(debug=True)