GOAL = "#GOAL: Script to run on Pop!OS 22.04 to clone the latest version of the Linux kernel, compile it and run it in QEMU such that there's a hello world C program running on that kernel (not running on the host system) and outputting the text: hello world. This script is running as root."

import os
import ast
import typing

import openai

# Import the code module
import code
import traceback
from io import StringIO
from contextlib import redirect_stdout

def trim_long_text(txt, length_trigger = 300) -> str:
  amount_over = len(txt) - length_trigger
  if amount_over > 0:
    middle_idx = len(txt) // 2
    return txt[:middle_idx - amount_over // 2] + " ... " + txt[middle_idx + amount_over // 2:]
  return txt[:]

def isValidPythonStatement(statement: str) -> bool:
  try:
    ast.parse(statement)
  except SyntaxError:
    print(f"\nThe statement to test: {statement} does not have the structure of a valid Python statement.", end="")
    return False
  if getFirstStatement(statement) is None:
    return False
  return True

def getFirstStatement(code: str) -> typing.Optional[str]:
  # parse the code into an abstract syntax tree
  tree = ast.parse(code)
  if len(tree.body) <= 0:
    return None
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
        self.prompt = ""
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
            push_return_value = None
            with redirect_stdout(stdout_capture):
              full_statement = command
              if not command.endswith("\n"):
                full_statement += "\n"
              push_return_value = super().push(full_statement)
            self._flush_output(stdout_capture)
            if push_return_value != False:
              self.append_output_to_prompt(f"Failed executing command in interactive terminal")
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

    def delete_last_command(self):
      idx = self.prompt.rfind("\n>>>")
      if idx >= 0:
        self.callback_command_string(f"\nDELETE {self.prompt[idx+1:]}")
        self.prompt = self.prompt[:idx]
   

openai.api_key = os.getenv("OPENAI_API_KEY")

#engines = openai.Engine.list()
#for engine in engines["data"]:
#   print(f"{engine}")

reset_passages =\
[\
"We've hit a dead end, it's time to pursue another strategy now.",
"We've reached an impasse; it's now necessary to explore a different approach.",
"We've come to a standstill; it's time to adopt a new tactic.",
"Having reached a deadlock, we must now seek an alternative plan.",
"We've encountered a roadblock; the moment has come to try a different method.",
]

def choose_reset_passage(seed: int) -> str:
  return reset_passages[seed % len(reset_passages)]


class SentientAi():
  def __init__(self):
    self._invalid_statement_count = 0
    self._unstuck_number = 2
    
    self._temperature = 0.9

    # Create an instance of the custom console class
    self.console = MyConsole()
    self.console.callback_command_string = print_string
    self.console.callback_output_string = print_string

    self.console.push(GOAL)
    self.console.push("#First verify that duckduckgo-search is installed and that we can get basic search results:")
    self.console.push("import subprocess")
    self.console.push(\
'''def install_python_package(package_name: str):
  command = "python -m pip install duckduckgo-search"
  process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
  ("output: " + str(output)) if output else None
  ("error: " + str(error)) if error else None'''\
)
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
    self.console.push("#Now the full script itself:")
    
    self.console.callback_command_string = do_not_print_string

  
  def loop(self):
    for i in range(100):
      input("\nPress ENTER to call OpenAI")
      extended_prompt = self.console.prompt + "\n>>>"
      messages=[
        {"role": "system", "content": "Your job is to complete the code by adding a single Python statement in your response. Learn from errors in the shell history. You can't change past statements, only add new ones. The code doesn't have to be finished, only write the very next, most likely Python statement. In the python script, always try to strive towards the user provided initial GOAL as fast as possible. Learn from mistakes and try to fix them. For example: if an error has been encountered: 'command git not found' then try to install git by running 'sudo apt install git'. Another example: If you receive an error that a specific Python library import failed, then try to use pip install to fix the issue. If you see the same approach being tried multiple times without success, try to gather more information: for example call 'ls' in the CWD or search the web."},
        {"role": "user", "content": "I will provide a Python interactive shell terminal output, please respond with the very next most likely Python statement. Respond with nothing but code. Now answer a boolean value of whether you understand the instructions."},
        {"role": "assistant", "content": "True"},
        {"role": "user", "content": "Let's try an example:\n>>>#print hello\n>>>"},
        {"role": "assistant", "content": "\"hello\""},
        {"role": "user", "content": ">>>#print hello\n>>>\"hello\"\nhello\n>>>#Now let's count until 5\n>>>"},
        {"role": "assistant", "content": "for i in range(5):\nprint(i)"},
        {"role": "user", "content": ">>>#print hello\n>>>\"hello\"\nhello\n>>>#Now let's count until 5\n>>>" +\
'''Traceback (most recent call last):
  File "<pyshell#0>", line 1, in <module>
    exec("for i in range(5):\nprint(i)")
  File "<string>", line 2
    print(i)
    ^^^^^
IndentationError: expected an indented block after 'for' statement on line 1
''' + ">>>"},
        {"role": "assistant", "content": "for i in range(5):\n  print(i)"},
        {"role": "user", "content": ">>>#print hello\n>>>\"hello\"\nhello\n>>>#Now let's count until 5\n>>>for i in range(5):\n  print(i)\n>>>1\n2\n3\n4\n5\n>>>#I see you understood the example. Let's continue now."},
        {"role": "user", "content": extended_prompt}
      ]
      response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
        temperature = self._temperature,
        frequency_penalty=0.7,
        max_tokens=len(extended_prompt) + 512,
      )
      response_text = response['choices'][0]['message']['content'].strip()
      if not isValidPythonStatement(response_text):
        self._invalid_statement_count += 1
        if self._invalid_statement_count >= self._unstuck_number:
          # Avoid getting stuck in a feedback loop
          self.console.callback_command_string = print_string
          if self._invalid_statement_count > self._unstuck_number:
            # Avoid placing multiple unstuck sentences in a row to in the prompt.
            self.console.delete_last_command()
          self.console.push(f"#{choose_reset_passage(self._invalid_statement_count)} back to the code now:")
          self.console.callback_command_string = do_not_print_string
        continue
      
      first_python_statement: str = getFirstStatement(response_text)
      input(f"\n>>>{first_python_statement}")
      #print(f"\n>>>{first_python_statement}")
      if not self.console.push(first_python_statement):
        # Error occurred running the statement
        self._invalid_statement_count += 1
      else:
        self._invalid_statement_count = 0

sentientAi = SentientAi()
sentientAi.loop()
