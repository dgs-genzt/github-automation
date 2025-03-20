# github-automation
A set of Python code to maintain Security and integrity of github repos in and across organization 


## Ruleset
A System to manage ruleset integrity across multiple repositories and organization. 

Add Repo and ruleset mapping information under rulesets/mapping folder (note: the mapping file name must be same as organization name)

Add new rules in json file format in rulesets/rules folder 

A commit to the mapping file of a particular organization in main branch will trigger the script and apply the rules for each repo in the organization 


## Teams
A System to manage teams and permissions assigned to teams across multiple repositories and organization. 

Add or Edit repo and teams and permission information in mapping file under teams/mapping folder (note: the mapping file name must be same as organization name)

A commit to the mapping file of a particular organization in main branch will trigger the script and apply the rules for each repo in the organization 
