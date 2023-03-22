import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

prompt=\
'''
You have now entered code chat mode.
You now have the ability to run Python code by appending it
to the chat.
Any response you give will be executed as Python code and
if you set a variable named "talkback" to a string value,
that reponse will be added to the chat,
and you will be able to use the new information gathered
from the "talkback" variable for the purpose of being more interactive.
Example of what the history chat is supposed to look like:
1. from duckduckgo_search import ddg\nfirst_result = ddg("Linux kernel CVEs")[0]\ntalkback = first_result["title"] + first_result["body"]
talkback: Linux Kernel CVEs | Linux Kernel Vulnerability TrackerLinux Kernel CVEs This is a simple project to track CVEs in the upstream ...
2. import sys\nfrom subprocess import PIPE, run\ncommand = [sys.executable, '-m', 'pip', 'install', 'requests']\nresult = run(command, stdout=PIPE, stderr=PIPE, universal_newlines=True)\ntalkback = f"ret: {result.returncode}, stdout: {result.stdout}, stderr: {result.stderr}"
talkback: ret: 0, stdout: Requirement already satisfied: requests in ...

You're running on Windows 10.
The goal is to use whatever resources you can to turn on mouse trails on my computer ASAP.

History:
'''
for i in range(15):
  real_prompt = prompt + "\ncurrent response:\n"
  print(f"prompt: {real_prompt}")
  response = openai.Completion.create(
    model="text-davinci-003",
    prompt=real_prompt,
    temperature=0.9,
    max_tokens=4000 - len(real_prompt),
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0
  )

  print(f"Output: {response}")

  response_text = response.choices[0].text
  prompt += f"\n{i + 1}. {response_text}"
  exec_success = False
  try:
    exec(response.choices[0].text)
    exec_success = True
  except Exception as e:
    prompt += f"\nerror: {e}"
  if exec_success:
    try:
      prompt += f"\ntalkback: {talkback}"
    except NameError:
      prompt += f"\ntalkback: undefined"

