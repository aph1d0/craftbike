# serwis_crm
   
Installation Requirements
============

1. Python3
2. Mysql
2. pip3
3. virtualenv

Installation Steps
============

1. Create a virtual environment using the following commands
    .. code-block:: python
    
        virtualenv -p python3 serwis_crm
        source serwis_crm/bin/activate
    
        
2. Now create the configuration file using the command
    .. code-block:: python
    
        cp config_vars.example config_vars.py
        
    Open the config_vars.py file and add the database connection 
    parameters in the PRODUCTION DATABASE SETTINGS (Default). 
    
    You can also setup the development and testing settings if you wish to.
        
3. Install the dependencies
   .. code-block:: python

       pip3 install -r requirements.txt

4. Create the following environment variables
   .. code-block:: python
   
       EMAIL_USER = <your username>
       EMAIL_PASS = <your password>
       
   If you want to run flask in development or testing mode set
   the following environment variable in addition to the above.
   .. code-block:: python
   
       FLASK_ENV = development, or
       FLASK_ENV = testing
   
5. Run the command
   .. code-block:: python
   
       python3 run.py
       
   This will run the installation wizard. Follow the instructions
   in the wizard and after finishing installation, stop the 
   application and start again by running the command in step #5.



