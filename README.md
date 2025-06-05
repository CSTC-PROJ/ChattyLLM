# ChattyLLM

## Description
A simple test to see what two LLM's might say to each other when prompted.  Using a sinle Ollama instance, two flask API's running on 5000 and 5001 will submit their responses to each other.

## Requirements
* Python 3.something
* Ollama (tested on windows)

## Steps
* Install Ollama
* Ollama pull llama3
* open a terminal and "python pa.py"
* open a new terminal and "python pb.py"
* open a command prompt and
* ```bash
  curl -X POST http://127.0.0.1:5001/chat -H "Content-Type: application/json" -d "{\"message\": \"My name is Jill tell me about  yourself\"}"
  ```

  The Curl request invokes the initial chat and each subsequent response writes to a file called "convo.txt" while submitting the response to the other running flask API

  Read the convo.txt

  ## Notes
  It's best to keep an eye on the respective running applications in the terminal as sooner or later the chats run their course and need terminating... or don't and see what happens.
