# Sitebuilder Interactions Terminal Program

## Purpose
This program facilitates the automation of various tasks, undertaken by the Service Analysts team, that pertain to interactions with Sitebuilder.

### Attended tasks
The following is a list of tasks that can be completed with use of the terminal program: -

- ACL creation
- Impact factors updates
- Rankings updates
- PPV updates
- TrendMD widget creation

### Data Structure

All but ACL Creations require a supplementary data csv to be provided to inform what values need to be changed for which site. The file data structures are as follows.

**if.csv**

| url_shortcode | One year | Five year |
| ----------- | ----------- | ----------- |
| brain | 11.1 | 12.592 |
| sleep | 123 | 4.56 |
| etc | etc | etc |


--------------------------------

**ranking.csv**

| url_shortcode | Ranking Category | Ranking |
| ----------- | ----------- | ----------- |
| brain | Ranking 1 | 0 out of 0 |
| sleep | Ranking 1 | 0 out of 0 |
| sleep | Ranking 2 | 0 out of 0 |
| etc | etc | etc |


--------------------------------


**ppv.csv**


| url_shortcode | GBP | EUR | USD |
| ----------- | ----------- | ----------- | ----------- |
| brain | 100 | 100 | 100 |
| sleep | 100 | 100 | 100 |
| etc | etc | etc | etc |


--------------------------------


**trendmd.csv**


| url_shortcode | id |
| ----------- | ----------- |
| brain | 43567 |
| sleep | 12345 |

## Set up of sitebuilder interactions terminal program
Use these steps to set up the console program for use: -

---

Anaconda

1. Download and install Anaconda
2. Open Anaconda prompt
3. Change directory to the root location of the script
    1. `cd "C:\your\script\location`
4. Create a new virtual environment and activate it
    1. `conda create --name your-environment-name python=3.7`
    2. `conda activate your-environment-name`
5. Add the required dependencies from the "requirements.txt" file
    1. `pip install -r requirements.txt`
6. Create a file called "sitebuilder_secrets.py" and edit it to contain you sitebuilder login credentials (see "secrets_template.py")
7. Install the local modules
    1. `python install -e .`
8. Start the script with "run.py"
    1. `python run.py`
    
    
### Please note
All of the various interactions can only be run while off of the <company name> network. This also goes for when you are installing dependencies and creating virtual environments with Conda.

**_This code is meant for demonstation purposes only, as such, the code here will not run due to essential, identifiable, information being removed._**
