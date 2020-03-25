#!/usr/bin/env python

import sys
import boto3
import re

###################################################
# NO DELETE                                       #
#    - if true this will not delete any stacks#
#    - use --nodelete to test and prevent deletes #
#    - use --delete instead to allow deltes       #
###################################################
no_delete = True

navapi_all = r'.*nav.*'
navapi_prod = r'(navplatform.navapi.prod-\d{4})'
navapi_dev  = r'navplatform.navapi.dev-'
navapi_sess = "navplatform-navapi-sess"

curr_navapi_prod = "navplatform-navapi-prod-0036"
curr_navapi_dev  = "navplatform-navapi-dev-0136"
curr_navapi_sess = "navplatform-navapi-dev-0116"
#curr_navapi_all =  "navplatform-navapi-prod-0036|navplatform-navapi-dev-0136|navplatform-navapi-dev-0116"
curr_navapi_all =  curr_navapi_prod+"|"+curr_navapi_dev+"|"+curr_navapi_sess

stk = navapi_dev
what = "list"
who = "dev"
dry_run = True

domain = "cloud.mapquest.com."
hostedZoneId = "none"


def notices():
  print("!!! NOTE: as a precaution\n!!! you need to run with --delete to actually delete stacks")


def get_args():
  debug = 0
  global no_delete

  argcnt = len(sys.argv)

  if debug > 0:
    print("arg count =", argcnt)
    c = 0
    while (c < argcnt):
      print("arg{}: {}".format(c, sys.argv[c]))
      c = c + 1

  while argcnt > 1:
    argcnt = argcnt - 1
    if debug > 0: print("{}: is {}".format(argcnt, sys.argv[argcnt]))

    option = sys.argv[argcnt]
    if option == '--no_delete' or option == '-no_delete':
      no_delete = True

    if option == '--delete' or option == '-delete':
      no_delete = False
      print("!!!CAUTION... DELETE has been enabled ({})".format(no_delete))


def get_hosted_zone_id(dns_domain):
  global hostedZoneId
  debug = 0

  for hz in dns_domain.list_hosted_zones()['HostedZones']:
    match = re.match('/hostedzone/([A-Z0-9]+)', hz['Id'])
    if match and hz['Name'] == domain:
      hostedZoneId = match.group(1)
      if debug > 0:
        print("using hosted zone id for", z['Name'], "=", match.group(1))
      return hostedZoneId


def get_cnames(dns_domain):
  global hostedZoneId
  dname = r'navplatform-navapi-(dev|prod).*.cloud.mapquest.com'
  dval = r'(navplatform-navapi-(prod|dev)-[0-9]+).*.cloud.mapquest.com'
  startrname = "dev.navapi-sessions.cloud.mapquest.com."
  cnames = {}
  debug = 0

  rs = dns_domain.list_resource_record_sets(HostedZoneId=hostedZoneId, StartRecordName=startrname)['ResourceRecordSets']
  for r in rs:
    # look for dns name entry for navplatform-navapi prod or dev
    match = re.match(dname, r['Name'])
    if match:
       envname = match.group(1)

       # look to make sure this is CNAME
       match = re.match('CNAME', r['Type'])
       if match:
         for rr in r['ResourceRecords']:

           # get the value of the CNAME, this is active deploy
           m = re.match(dval, rr['Value'])
           if m:
             rrv = m.group(1)
             cnames[envname] = rrv
             if debug > 0:
               print(r['Name'], r['Type'], rrv, cnames[envname])
  if debug > 0:
    print(cnames)

  return cnames


def menu():
  global stk, what, who
  global dry_run

  dry_run = True

  ask_dry_run = False

  print("== Delete navapi stacks ==")
  print("0 - exit")
  print("1 - list dev  stacks")
  print("2 - list prod stacks")
  print("3 - list all  stacks")
  print("======")
  print("4 - delete dev  stacks")
  print("5 - delete prod stacks")
  print("6 - delete all  stacks")
  print("======")
  print("7 - delete stack by name")
  print("======")

  choice = input("??? what would you like to do? ")
  if choice == "0":
    exit()

  elif choice == "1":
    stk = navapi_dev
    what = "list"
    who = "dev"
    ask_dry_run = False

  elif choice == "2":
    stk = navapi_prod
    what = "list"
    who = "prod"
    ask_dry_run = False

  elif choice == "3":
    stk = navapi_all
    what = "list"
    who = "all"
    ask_dry_run = False

  elif choice == "4":
    stk = navapi_dev
    what = "delete"
    who = "dev"
    ask_dry_run = True

  elif choice == "5":
    stk = navapi_prod
    what = "delete"
    who = "prod"
    ask_dry_run = True

  elif choice == "6":
    stk = navapi_all
    what = "delete"
    who = "all"
    ask_dry_run = True

  elif choice == "7":
    stk = "custom"
    what = "delete"
    who = "by name"
    ask_dry_run = True

  else:
    print("please make a valid selection")
    exit(0)

  print("--- you chose to", what, who, "stacks... ", end="")
  print("(",stk, ")")

  ans = "N"
  ans = input("??? do you wish to continue? (y/n) ")

  if ans == "yes" or ans == "y" or ans == "Y":

    if ask_dry_run:
      a = input("before actual delete, would you like to perform a dry run? ")

      if a == "yes" or a == "y" or a == "Y":
        dry_run = True
      else:
        dry_run = False

    if dry_run and (what == "delete"):
      print('continuing in "dry run" mode')
    elif what == "delete":
      print('continuing LIVE!')


  elif ans == "no" or ans == "n" or ans == "N":
    print("exiting")
    exit(0)

  else:
    print("please make a valid selection")
    exit(1)

  if choice == "7":
    stk = input("Enter then stack name you wish to delete ")
    print("delete:", stk + "?")
    ans = input("??? do you wish to continue deleting? ")

  return int(choice)


def print_stacks(stacks):
  for s in stacks:
    print(s['StackName'])


def print_stacks_matching(stacks, matching):
  print("(*) == denotes current CNAME stack")
  for s in stacks:
    if re.match(matching, s['StackName'], flags=0):
      if re.match(curr_navapi_all, s['StackName'], flags=0):
        print("*",s['StackName'])
      else:
        print(s['StackName'])


def describe_stacks_matching(cfn, matching):
  stks = cfn.describe_stacks()
  for s in stks:
    match = re.match(matching, s['StackName'])
    if match:
      print("->", match.group(0))


def describe_stacks(cfn):
  stacks = {}
  stacks = cfn.describe_stacks()['Stacks']
  return stacks


def describe_stack_resource(cfn, sname, resource):
  response = {}
  response = cfn.describe_stack_resource(sname, **resource)
  return response


def delete_stack(cfn, matching, resource):
  resource = {}
  #response = cfn.delete_stack(cfn, sname)
  if re.match(matching, s['StackName'], flags=0):
    response = cfn.describe_stack_resource(matching, resource)


def delete_stacks_matching(cfn, stacks, matching):
  global no_delete

  count = 0
  for s in stacks:
    match = re.match(matching, s['StackName'], flags=0)
    if match:
      if not re.match(curr_navapi_all, s['StackName'], flags=0):
        count = count + 1
        sname = match.group(0)
        print("")
        print("response = cfn.delete_stack(StackName={}) ***".format(sname))
        print(count, "Deleting stack {}".format(s['StackName']))
        if not dry_run and not no_delete:
          response = cfn.delete_stack(StackName=sname)
        else:
          print("DRY RUN: NO STACKS WERE HARMED DURING THIS TEST!")


def main():
  debug = 0
  global curr_navapi_prod
  global curr_navapi_dev
  global curr_navapi_all
  global no_delete


  if len(sys.argv) > 1:
    get_args()

  if debug > 0:
    print("ARGUMENTS: no_delete={}".format(no_delete))

  if no_delete:
    notices()

  print("...please wait while we query route53...")
  r53 = boto3.client('route53')
  hostedZoneId = get_hosted_zone_id(r53)

  if debug > 0: print("hostedZoneId =", hostedZoneId)

  if debug > 0: print("getting CNAMEs...")
  c = get_cnames(r53)

  if debug > 0:
    print("CNAMES:",c)
    print("CNAME/prod:", c['prod'])
    print("CNAME/dev:", c['dev'])
    print("CNAME/sess:", curr_navapi_sess)

  if debug > 0:
    print("*** Existing Deployment Values ***")
    print("EXISTING:", "PROD:", curr_navapi_prod)
    print("EXISTING:", "DEV: ", curr_navapi_dev)
    print("EXISTING:", "SESS:", curr_navapi_sess)

  if debug > 0: print("*** Setting Current Deployment Values ***")
  curr_navapi_prod = c['prod']
  curr_navapi_dev  = c['dev']

  curr_navapi_all =  curr_navapi_prod+"|"+curr_navapi_dev+"|"+curr_navapi_sess

  if debug > 0:
    print("*** NEW Deployment Values ***")
    print("NEW:", "PROD:", curr_navapi_prod)
    print("NEW:", "DEV: ", curr_navapi_dev)
    print("NEW:", "SESS:", curr_navapi_sess)


  ans = menu()

  cf = boto3.client('cloudformation')

  stacks = describe_stacks(cf)

  # LIST STACKS
  if ans < 4:
    print_stacks_matching(stacks, stk)

  elif ans <= 6:
    delete_stacks_matching(cf, stacks, stk)

  elif ans == 7:
    delete_stacks_matching(cf, stacks, stk)



if __name__ == "__main__":
  main()

