# codetools
LSST DM SQuaRE misc. code management tools

Example usage
-------------

To generate a personal user token (you will be prompted for your password):

    github_auth.py
  
To generate a token with delete privileges, set your DM_SQUARE_ADMIN env variable before running the above.

To clone all LSST org repos in an org called (yourusername)-shadow 

    github_fork_repos.py
    
This is useful for testing tools in this suite safely.

If you want to take a recent fork, you will need to delete the existing shadow repos first:

github_delete_shadow.py

That requires a token with delete privileges. 

To get more debugging information, set your DM_SQUARE_DEBUG variable before running any command. 

Dependencies
------------

- github3.py
