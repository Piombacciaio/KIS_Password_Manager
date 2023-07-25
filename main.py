"""Keep It Simple Password Manager by Piombacciaio"""
import colorama, ctypes, difflib, hashlib, json, msvcrt, os, secrets, sys
from colorama import Fore
from cryptography.fernet import Fernet
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTP

#CONSTS
BASE_PATH = r"C:\KIS Password Manager"
CONFIG_PATH = f"{BASE_PATH}\\config.json"
KEYS_PATH = f"{BASE_PATH}\\Keys"
STORAGE_PATH = f"{BASE_PATH}\\Storage"
DEFAULT_CONFIG = """
{
  "profiles": {
    "username": {
      "access": "xxx:xxx:xxx",
      "mail": "example@example.com"
    }
  },
  "otp_account":{
    "email": "CHANGE_TO_YOUR_ADDRESS",
    "password": "CHANGE_TO_YOUR_PASSWORD"
  }
}
"""

#INIT
colorama.init()
ctypes.windll.kernel32.SetConsoleTitleW(f'Keep It Simple Password Manager | made by piombacciaio')

text="Piombacciaio" #Text for the clickable link
target = "https://github.com/Piombacciaio" #Actual link

if not os.path.exists(BASE_PATH):
  os.mkdir(BASE_PATH)

if not os.path.exists(KEYS_PATH):
  os.mkdir(KEYS_PATH)

if not os.path.exists(STORAGE_PATH):
  os.mkdir(STORAGE_PATH)

if not os.path.exists(CONFIG_PATH):
  with open(CONFIG_PATH, "w") as f:
    f.write(DEFAULT_CONFIG)

#FUNCS
def clear():
  """Unified command for cleaning the screen"""
  os.system("cls")

def get_pass():
  """Hides user input with * and returns it"""
  pw = ""
  print(">> ", end="", flush=True)
  while True:
    char = msvcrt.getwch()
    if char == "\r" or char == "\n":
      print("", flush=True)
      break
    if char  == '\003':
      raise KeyboardInterrupt
    elif char == "\b":
      if len(pw) > 0:
        pw = pw[:-1]
        sys.stdout.write("\b")
        print(" ", end="", flush=True)
        sys.stdout.write("\b")
    else:
      print("*", end="", flush=True)
      pw += char
  return pw

def err_print(text:str, severity:int = 0, end="\n"):
  """Print a pre-formatted version of an error message. severity determines text colo
  0 : green text
  1 : yellow text
  2 : red text"""
  if severity == 0: print(f"{Fore.GREEN}ERROR{Fore.RESET} - {text}", end=end)
  if severity == 1: print(f"{Fore.YELLOW}ERROR{Fore.RESET} - {text}", end=end)
  if severity == 2: print(f"{Fore.RED}ERROR{Fore.RESET} - {text}", end=end)

def otp_check(email:str, subject:str = None):
  """Check an email address using OTP generation"""
  server = SMTP("smtp.gmail.com", 587)
  server.starttls()
  server.ehlo()
  server.login(EMAIL, PASSWORD)
  otp_code = "".join(str(secrets.randbelow(10)) for _ in range(6))
  contact_message = MIMEMultipart("Alternative")
  contact_message["Subject"] = subject
  contact_message["Bcc"] = email
  contact_message["From"] = EMAIL
  html = f"""<div><h1 style="color:#5e9ca0;text-align:center">HELLO!</h1></div><div><h2 style="color:#2e6c80;text-align:center">we have received an OTP request for this address.</h2></div><br><div><p>Your code is: {otp_code}</p><p>Have a nice day!<br>- Hello OTP team</p><br><p>If this request didn't came from you, don't worry, you can delete this email.</p></div>"""
  contact_message.attach(MIMEText(html, "html"))
  try:
    server.sendmail(EMAIL, email, contact_message.as_string())
  except Exception as e:
    err_print(f"Failed to send mail. Error: {e}. Press ENTER to continue.", 2, end="")
    input()
  user_otp = input("Enter OTP code >> ")
  if user_otp == otp_code:
    if "Verification" in subject.lower(): print(f"OTP match. {email} is now verified.")
    return 1
  else:
    if "Verification" in subject.lower(): print("OTP mismatch. To retry login and go to \"add/update otp mail\"")
    return 0

def login():
  """Login to an existing account"""
  with open(CONFIG_PATH, "r") as f:
    config = json.load(f)
  print(f"{Fore.GREEN}LOGIN{Fore.RESET}\n")
  username = input("Please provide a username\n>> ").lower()
  password = get_pass()
  if username in config["profiles"]:
    pepper, salt, access = config["profiles"][username]["access"].split(":")
    password = salt + password + pepper
    hashed_password = hashlib.sha512(password.encode("utf-8")).hexdigest()
    if hashed_password == access:
      return username
    else:
      err_print("Invalid Username Or Password. Press ENTER to continue.", 1, "")
      input()
  else:
    err_print("Invalid Username Or Password. Press ENTER to continue.", 1, "")
    input()

def register():
  """Create new user inside config.json"""
  with open(CONFIG_PATH, "r") as f:
    config = json.load(f)
  print(f"{Fore.GREEN}REGISTRATION PROCESS{Fore.RESET}\n")
  username = input("Please choose a username\n>> ")
  while username in config["profiles"]: #Retry if username already exists in config
    err_print("Invalid Username. Please Retry.", 1)
    username = input(">> ")
  username = username.lower()
  email = input("Please insert your email >> ")
  check = otp_check(email, "Verification")
  print("Please choose a password [min. 10 chars]")
  password = get_pass()
  while len(password) < 10:
    err_print("Password Too Short. Please Retry.", 1)
    password = get_pass()
  salt = secrets.token_urlsafe(128)
  pepper = secrets.token_urlsafe(128)
  password = salt+password+pepper
  hashed_password = hashlib.sha512(password.encode("utf-8")).hexdigest()
  password = ""
  access = pepper + ":" + salt + ":" + hashed_password
  config["profiles"][username] = {}
  config["profiles"][username]["access"] = access
  config["profiles"][username]["email"] = email if check == 1 else None
  with open(CONFIG_PATH, "w") as f:
    json.dump(config, f, indent=4)
  key = Fernet.generate_key()
  with open(f"{KEYS_PATH}\\{hashlib.sha512(username.encode('utf-8')).hexdigest()}.key", "wb") as f:
    f.write(key)
  with open(f"{STORAGE_PATH}\\{username}.pass", "w") as f:
    f.write("""{  
    }""")
  print(f"{Fore.GREEN}SUCCESS{Fore.RESET} New user has been registered. You may now proceed to login, press ENTER to continue.", end="")
  input()

def recover_access():
  """The classic recover password in case user forgets it"""
  with open(CONFIG_PATH, "r") as f:
    config = json.load(f)
  username = input("Provide your username >> ").lower()
  if username in config["profiles"]:
    email = config["profiles"][username]["email"]
    check = otp_check(email, "Password recovery")
    if check == 1:
      print("OTP Match. Please enter new password.")
      new_pw = get_pass()
      pepper, salt, _ = config["profiles"][username]["access"].split(":")
      password = salt + new_pw + pepper
      hashed_password = hashlib.sha512(password.encode("utf-8")).hexdigest()
      new_pw = ""
      access = pepper + ":" + salt + ":" + hashed_password
      config["profiles"][username]["access"] = access
      with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)
      print(f"{Fore.GREEN}SUCCESS{Fore.RESET} New password has been set. You may now proceed to login, press ENTER to continue.", end="")
      input()
    else:
      err_print("Invalid OTP. Please retry.", 1, "")
      input()
  else:
    err_print("Invalid Username. Press ENTER to continue.", 1, "")
    input()
    
def main():
  while True:
    clear()
    print(f"\n{Fore.GREEN}Keep It Simple Password Manager{Fore.RESET} by \u001b]8;;{target}\u001b\\{text}\u001b]8;;\u001b\\\n")#This monstrosity just displays a clickable "Piombacciaio" using escape chars
    print(f"[{Fore.GREEN}L{Fore.RESET}] - Login\n[{Fore.GREEN}R{Fore.RESET}] - Register\n[{Fore.GREEN}H{Fore.RESET}] - Recover Access\n[{Fore.GREEN}Q{Fore.RESET}] - Quit")
    command = input(">> ").upper()
    while command not in ["L", "R", "H", "Q"]: #Force the user to choose one of the valid options
      err_print("Invalid Choice. Press Enter to continue...", 1, end="")
      input()
      command = input(">> ").upper()
    clear()
    if command == "Q": # QUIT PROGRAM
      exit(0)
    if command == "L": # LOGIN
      username = login()
      while username != None:
        clear()
        print(f"\n{Fore.GREEN}Keep It Simple Password Manager{Fore.RESET} by \u001b]8;;{target}\u001b\\{text}\u001b]8;;\u001b\\")#This monstrosity just displays a clickable "Piombacciaio" using escape chars
        print(f"{Fore.GREEN}Welcome{Fore.RESET} {username}\n")
        print(f"[{Fore.GREEN}A{Fore.RESET}] - Add password\n[{Fore.GREEN}D{Fore.RESET}] - Delete password\n[{Fore.GREEN}R{Fore.RESET}] - Read password\n[{Fore.GREEN}U{Fore.RESET}] - Update email\n[{Fore.GREEN}K{Fore.RESET}] - Delete account ({Fore.RED}Action not reversible{Fore.RESET})\n[{Fore.GREEN}L{Fore.RESET}] - Logout")
        command = input(">> ").upper()
        while command not in ["A", "D", "R", "K", "U", "L"]: #Force the user to choose one of the valid options
          err_print("Invalid Choice. Press Enter to continue...", 1, end="")
          input()
          command = input(">> ").upper()
        if command == "A": # ADD PASSWORD servicename:{username:"", password:""}
          with open(f"{STORAGE_PATH}\\{username}.pass", "r") as f:
            storage = json.load(f)
          servicename = input("Please provide a unique name >> ")
          while servicename in storage:
            err_print("Invalid Name. Please Retry.", 1)
            servicename = input(">> ")
          print("Please provide the username for the service ", end="")
          user = get_pass()
          print("Please provide the password for the service ", end="")
          password = get_pass()
          with open(f"{KEYS_PATH}\\{hashlib.sha512(username.encode('utf-8')).hexdigest()}.key", "rb") as f:
            key = f.read()
          enc_user = Fernet(key).encrypt(user.encode()).decode()
          enc_pw = Fernet(key).encrypt(password.encode()).decode()
          storage[servicename] = {}
          storage[servicename]["username"] = enc_user
          storage[servicename]["password"] = enc_pw
          with open(f"{STORAGE_PATH}\\{username}.pass", "w") as f:
            json.dump(storage, f, indent=4)
        if command == "D": # DELETE PASSWORD
          with open(f"{STORAGE_PATH}\\{username}.pass", "r") as f:
            storage = json.load(f)
          servicename = input("Please provide a service name >> ")
          if servicename in storage:
            print(f"Do you really want to delete the selected password? [Y/N]\n{Fore.RED}ATTENTION THIS CAN'T BE UNDONE{Fore.RESET}")
            choice = input(">> ").upper()
            while choice not in ["Y", "N"]: #Force the user to choose one of the valid options
              err_print("Invalid Choice. Press Enter to continue...", 1, end="")
              input()
              choice = input(">> ").upper()
            if choice == "N":
              print("Aborting operation. Press ENTER to continue.", end="")
              input()
            if choice == "Y":
              del storage[servicename]
              with open(f"{STORAGE_PATH}\\{username}.pass", "w") as f:
                json.dump(storage, f, indent=4)
              print("Deletion completed. Press ENTER to continue", end="")
              input()
          else:
            err_print("Invalid Name. Press Enter to continue...", 1, end="")
            input()
        if command == "R": # READ PASSWORD
          print(f"[{Fore.GREEN}S{Fore.RESET}] - Search for service name\n[{Fore.GREEN}L{Fore.RESET}] - List all service names\n[{Fore.GREEN}R{Fore.RESET}] - Read password from storage")
          choice = input(">> ").upper()
          while choice not in ["S", "R", "L"]: #Force the user to choose one of the valid options
            err_print("Invalid Choice. Press Enter to continue...", 1, end="")
            input()
            choice = input(">> ").upper()
          with open(f"{STORAGE_PATH}\\{username}.pass", "r") as f:
            storage = json.load(f)
          with open(f"{KEYS_PATH}\\{hashlib.sha512(username.encode('utf-8')).hexdigest()}.key", "rb") as f:
            key = f.read()
          if choice == "S":
            services = list(storage.keys())
            search = input("Please provide a term to search >> ")
            result = difflib.get_close_matches(search, services, len(services), 0.4)
            print(f"All similar terms to {search} are:\n{result}\nWhen done, press ENTER to continue.", end="")
            input()
          if choice == "R":
            servicename = input("Please provide a service name >> ")
            if servicename in storage:
              enc_user:str = storage[servicename]["username"]
              enc_pw:str = storage[servicename]["password"]
              user = Fernet(key).decrypt(enc_user.encode()).decode()
              password = Fernet(key).decrypt(enc_pw.encode()).decode()
              print(f"The username/password combo for {servicename} is:\n- Username: {user}\n- Password: {password}\nWhen done, press ENTER to continue.", end="")
              input()
            else:
              err_print("Invalid Name. Press Enter to continue...", 1, end="")
              input()
          if choice == "L":
            services = list(storage.keys())
            print(f"The following services have a username/password combo saved:\n{services}\nWhen done, press ENTER to continue.", end="")
            input()
        if command == "K": #DELETE ACCOUNT
          print(f"Do you really want to delete the account? [Y/N]\n{Fore.RED}ATTENTION THIS CAN'T BE UNDONE{Fore.RESET}")
          choice = input(">> ").upper()
          while choice not in ["Y", "N"]: #Force the user to choose one of the valid options
            err_print("Invalid Choice. Press Enter to continue...", 1, end="")
            input()
            choice = input(">> ").upper()
          if choice == "N":
            print("Glad to see you stayin'. Press ENTER to continue.", end="")
            input()
          if choice == "Y":
            print("Deleting all your data. Please wait.")
            del config["profiles"][username]
            with open(CONFIG_PATH, "w") as f:
              json.dump(config, f, indent=4)
            os.remove(f"{STORAGE_PATH}\\{username}.pass")
            os.remove(f"{KEYS_PATH}\\{hashlib.sha512(username.encode('utf-8')).hexdigest()}.key")
            print("Deletion completed. Press ENTER to continue", end="")
            input()
            break
        if command == "U": #UPDARE EMAIL
          new_mail = input("Please provide a new email address >> ")
          check = otp_check(new_mail, "Email Update")
          if check == 1:
            config["profiles"][username]["email"] = new_mail
            with open(CONFIG_PATH, "w") as f:
              json.dump(config, f, indent=4)
            print(f"{Fore.GREEN}SUCCESS{Fore.RESET} New email has been set. Press ENTER to continue.", end="")
            input()
          else:
            err_print("Invalid OTP. Please retry.", 1, "")
            input()
        if command == "L": #LOGOUT
          break
    if command == "R": #REGISTER USER
      register()
    if command == "H": #RECOVER ACCESS
      recover_access()
if __name__ == "__main__": 
  with open(CONFIG_PATH, "r") as f:
    config = json.load(f)
  EMAIL = config["otp_account"]["email"] if config["otp_account"]["email"] != "CHANGE_TO_YOUR_ADDRESS" else (err_print("Change OTP Email Address To Your Own In Config File. Press ENTER To Quit.", 2, ""), input(), quit(0))
  PASSWORD = config["otp_account"]["password"] if config["otp_account"]["password"] != "CHANGE_TO_YOUR_PASSWORD" else (err_print("Change OTP Email Password To Your Own In Config File. Press ENTER To Quit.", 2, ""), input(), quit(0))
  main()