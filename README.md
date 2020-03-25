# manage_stacks
find unused stacks and delete them

Problem:
NavAPI have been building their code and deploying them as flask artifacts to new stacks within AWS...
We can debate the merits of doing this versus using a prexisting, already warmed stack (loadbalancer) later.
As new stacks are deployed, the old/currently existing stacks have never been deleted (we are paying for these) 

Solution:
Immediate... and the purpose of this script is to delete all but those stacks that are currently in use.
Long term... we won't need this script, new stacks will either be updated to run on existing stacks or we will insure that, as part of the delivery process, the old stacks will be destroyed.

Notes and Idiosyncrasies:
1 - this environment was inherited
2 - I have no knowledge or understanding of how we got to this point
3 - I have been giving a list of several stacks that cannot be destroyed
4 - in addition, the current in use production stack and dev stacks cannot be destroyed
Stacks:
curr_navapi_prod = "navplatform-navapi-prod-0036"
curr_navapi_dev  = "navplatform-navapi-dev-0136"
curr_navapi_sess = "navplatform-navapi-dev-0116"
curr_navapi_all  =  curr_navapi_prod+"|"+curr_navapi_dev+"|"+curr_navapi_sess

Regardless of your selection in the menu, the above stacks, and/or the replacements found in Route53 will NOT be deleted by this script - they will need to be deleted manually using aws cli or the GUI... this is just another precaution.  
Even if you select "delete ALL stacks" these stacks will not be removed.

You may enter the stacks you wish to delete using a regular expression... as I did not create the names of these stacks, I don't have much control over what can or cannot be deleted by using a regex... use caution, and don't be greedy with your regex!  Be more specific to limit the range of stacks that can be deleted.

Precautions:
Because I tend to wear a belt and suspenders, I don't trust myself or my abilities to not delete more than I should :)
therefore, unless you explicitly use the --delete flag, the stacks will not be deleted, but a list of what would be delete will be displayed.

Likewise, we will take a (more or mostly less) approach of treating this as a finite state machine which is menu driven
This is just to add additional precautions.

There is a "dry-run" option that is hard-coded to True... again, with the express intent to to accidentally delete anything

###################################################
# NO DELETE                                       #
#    - if true this will not delete any stacks    #
#    - use --nodelete to test and prevent deletes #
#    - use --delete instead to allow deltes       #
###################################################
no_delete = True

Menu Selections:
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


