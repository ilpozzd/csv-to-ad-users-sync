import ldap, ldap.modlist
import os
import csv

def getUserObjectByMail(mail: str, attributes: list):
  return ldapConnection.search_s(os.environ.get("AD_SUFFIX"), ldap.SCOPE_SUBTREE, filterstr=f"(&(objectclass=user)(mail={mail}))", attrlist=attributes)

try:
  with open(os.environ.get("DATA_FILE_PATH"), encoding="utf-8-sig") as csvfile:
    data = csv.DictReader(csvfile, delimiter='\t')
    users = [row for row in data]
except:
  print("Can't parse CSV file from " + os.environ.get("DATA_FILE_PATH"))
  exit(1)

try:
  ldapConnection = ldap.initialize(os.environ.get("DC_URL")) 
  ldapConnection.simple_bind_s(os.environ.get("DC_USERNAME"), os.environ.get("DC_PASSWORD"))
except ldap.SERVER_DOWN:
  print("Can't connect to LDAP server")
  exit(1)
except ldap.INVALID_CREDENTIALS:
  print("Can't authorize to LDAP server with given credentials")
  exit(1)

for user in users:
  userObject = getUserObjectByMail(user["mail"], user.keys())

  if not len(userObject):
    print(f"Cant't find user {user['mail']}")
    continue

  if user["manager"] != "":
    managerObject = getUserObjectByMail(user["manager"], ["mail"])
    if len(managerObject):
      user["manager"] = managerObject[0][0]
    else:
      print(f"Cant't find manager with {user['manager']} mail to user {user['mail']}")
      user["manager"] = ""

  old = {}
  new = {}

  for attr in user.keys():
    value = userObject[0][1][attr][0].decode("utf-8") if attr in userObject[0][1] else ""
    if value != user[attr]:
      old[attr] = [value.encode("utf-8")]
      new[attr] = [user[attr].encode("utf-8")]

  if len(old) and len(new):
    print(f"{user['mail']}:")
    for attr in new.keys():
      print(f"- {attr}: {old[attr][0].decode('utf-8')} -> {new[attr][0].decode('utf-8')}")

    try:
      ldapConnection.modify_s(userObject[0][0], ldap.modlist.modifyModlist(old, new))
    except:
      print("Can't write new attributes values to " + user["mail"])
    else:
      print("+ New attributes wrote successfully!")