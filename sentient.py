import os
import openai

import ast

# Import the code module
import code
import traceback
from io import StringIO
from contextlib import redirect_stdout

def trim_long_text(txt, length_trigger = 100) -> str:
  amount_over = len(txt) - length_trigger
  if amount_over > 0:
    middle_idx = len(txt) // 2
    return txt[:middle_idx - amount_over // 2] + " ... " + txt[middle_idx + amount_over // 2:]
  return txt[:]

def isValidPythonStatement(statement: str) -> bool:
  try:
    ast.parse(statement)
  except SyntaxError:
    print(f"The statement to test: {statement} does not have the structure of a valid Python statement.")
    return False
  return True

# Define a custom console class that captures the output
class MyConsole(code.InteractiveConsole):
    def __init__(self, locals=None, filename="<console>"):
        super().__init__(locals, filename)
        self.output = ""
        self.prompt = "Continue this Python terminal output, user input is not an option."
        
    def push(self, command):
        self.prompt += f"\n>>>{command}"
        stdout_capture = StringIO()
        try:
            # It's required to also capture the stdout output
            # because when an expression is evaluated, that causes
            # the write function to be called, and the string
            # is appended to self.output.
            # But when the command involved a manual print
            # then the only way to capture that is to capture
            # stdout itself.
            with redirect_stdout(stdout_capture):
                super().push(command)
            self._flush_output(stdout_capture)
        except Exception as e:
            self._flush_output(stdout_capture)
            self.prompt += trim_long_text(f"\n{traceback.format_exc()}")

    def _flush_output(self, stdout_capture: StringIO):
        print_outputs = stdout_capture.getvalue()
        if print_outputs != "":
            self.prompt += trim_long_text(f"\n{print_outputs}")
        if self.output != "":
            self.prompt += trim_long_text(f"\n{self.output}")
        self.output = ""

    def write(self, data):
        # Append the data to the output attribute
        self.output += data
        

openai.api_key = os.getenv("OPENAI_API_KEY")

#engines = openai.Engine.list()
#for engine in engines["data"]:
#   print(f"{engine}")

class SentientAi():
  def __init__(self):
    self._temperature = 0.7

    # Create an instance of the custom console class
    self.console = MyConsole()

    self.console.push("#The goal of this script is to automatically search the web for the latest Hank Green YouTube video and then open Google Chrome on the Windows computer with the link to that YouTube video.")
    self.console.push("#First verify that duckduckgo-search is installed and that we can get basic search results:")
    self.console.push("import subprocess")
    self.console.push("command = \"python -m pip install duckduckgo-search\"")
    self.console.push("process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)")
    self.console.push("output, error = process.communicate()")
    self.console.push("(\"output: \" + str(output)) if output else None")
    self.console.push("(\"error: \" + str(error)) if error else None")
    self.console.push("from duckduckgo_search import ddg")
    self.console.push("results = ddg(\"How to search Duck Duck Go programmatically using Python\")")
    self.console.push("first_result_header: str = results[0][\"title\"]")
    self.console.push("first_result_body: str = results[0][\"body\"]")
    self.console.push("#Now the full script:")


  def increaseTemperature(self, portion: float):
    diff = 1.0 - self._temperature
    self._temperature += diff * portion

  def decreaseTemperature(self, portion: float):
    diff = self._temperature - 0.0
    self._temperature -= diff * portion

  def loop(self):
    for i in range(15):
      input("\nPress ENTER to call OpenAI")
      extended_prompt = self.console.prompt + "\n>>>"
      response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
          {"role": "system", "content": "Run single line Python statements in the Python interactive shell."},
          {"role": "user", "content": extended_prompt}
        ],
        temperature = self._temperature,
        frequency_penalty=0.9,
        max_tokens=len(extended_prompt) + 512,
        stop="\n"
      )
      response_text = response['choices'][0]['message']['content'].strip()
      if not isValidPythonStatement(response_text):
        self.decreaseTemperature(0.5)
        continue
      else:
        self.increaseTemperature(0.25)
      print(self.console.prompt)
      input(f">>>{response_text}")
      self.console.push(response_text)

sentientAi = SentientAi()
sentientAi.loop()
