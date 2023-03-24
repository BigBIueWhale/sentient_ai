import os
import ast
import typing

import openai

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

def getFirstStatement(code: str) -> str:
  # parse the code into an abstract syntax tree
  tree = ast.parse(code)
  # get the first node in the body of the module
  first_node = tree.body[0]
  # return the source code of the first node
  return ast.unparse(first_node)

def do_not_print_string(_ = str) -> None:
  pass

def print_string(string = str) -> None:
  print(string, end='')

# Define a custom console class that captures the output
class MyConsole(code.InteractiveConsole):
    def __init__(self, locals=None, filename="<console>"):
        super().__init__(locals, filename)
        self.output = ""
        self.prompt = "Continue this Python terminal output, user input is not an option."
        self.callback_command_string: Callable[[str], None] = do_not_print_string
        self.callback_output_string: Callable[[str], None] = do_not_print_string

    def push(self, command) -> bool:
        self.append_command_to_prompt(command)
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
            self.append_output_to_prompt(trim_long_text(traceback.format_exc()))
            return False #Error occurred
        return True

    def _flush_output(self, stdout_capture: StringIO):
        print_outputs = stdout_capture.getvalue()
        if print_outputs != "":
            self.append_output_to_prompt(trim_long_text(print_outputs))
        if self.output != "":
            self.append_output_to_prompt(trim_long_text(self.output))
        self.output = ""

    def append_output_to_prompt(self, text: str):
      str_to_append = f"\n{text}"
      self.prompt += str_to_append
      self.callback_output_string(str_to_append)

    def append_command_to_prompt(self, command: str):
      str_to_append = f"\n>>>{command}"
      self.prompt += str_to_append
      self.callback_command_string(str_to_append)

    def write(self, data):
        # Append the data to the output attribute
        self.output += data
   

openai.api_key = os.getenv("OPENAI_API_KEY")

#engines = openai.Engine.list()
#for engine in engines["data"]:
#   print(f"{engine}")

class SentientAi():
  def __init__(self):
    self._invalid_statement_count = 0
    self._unstuck_number = 3
    
    self._temperature = 0.7

    # Create an instance of the custom console class
    self.console = MyConsole()
    self.console.callback_command_string = print_string
    self.console.callback_output_string = print_string

    self.console.push("#Search for the lastest exploit in the Linux kernel and then based on the results check if the computer that the Python interactive terminal is running on is vulnerable to that exploit. If the computer is vulnerable to the exploit, shut down the computer, if not: restart the computer.")
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
    self.console.push("first_result_link: str = results[0][\"href\"]")
    self.console.push("#Now the full script:")
    
    self.console.callback_command_string = do_not_print_string

  def loop(self):
    for i in range(15):
      input("\nPress ENTER to call OpenAI")
      extended_prompt = self.console.prompt + "\n>>>"
      response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
          {"role": "system", "content": "Run a single Python statements in the Python interactive shell and then stop responding."},
          {"role": "user", "content": extended_prompt}
        ],
        temperature = self._temperature,
        frequency_penalty=0.9,
        max_tokens=len(extended_prompt) + 512,
      )
      response_text = response['choices'][0]['message']['content'].strip()
      if not isValidPythonStatement(response_text):
        self._invalid_statement_count += 1
        if self._invalid_statement_count >= self._unstuck_number:
          # Avoid getting stuck in a feedback loop
          self.console.push("#That didn't work, let's try something else, and continue with the code:")
          self._invalid_statement_count = 0
        continue
      
      first_python_statement: str = getFirstStatement(response_text)
      input(f">>>{first_python_statement}")
      if not self.console.push(first_python_statement):
        # Error occurred running the statement
        self._invalid_statement_count += 1
      else:
        self._invalid_statement_count = 0

sentientAi = SentientAi()
sentientAi.loop()
