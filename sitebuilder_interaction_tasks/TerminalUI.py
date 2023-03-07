# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.6.0
#   kernelspec:
#     display_name: sitebuilder-interactions
#     language: python
#     name: sitebuilder-interactions
# ---

# +
import sys
from os.path import abspath, exists, join
from os import mkdir, listdir

from tqdm import tqdm, trange
import pandas as pd

from sitebuilder_interaction_tasks.ModifyFile import ModifyFile
from sitebuilder_interaction_tasks.AutomatedContentListings import AutomatedContentListings
from sitebuilder_interaction_tasks.SitebuilderSite import SitebuilderSite
from sitebuilder_interaction_tasks.SitebuilderInteraction import SitebuilderInteraction

class TerminalUI:
    '''
    UI to call the correct functions based on user selected options.
    '''
    
    current_dir = abspath("")
    
    def __init__(self):
        self.choices = {
            "1": self.acl_creation,
            "2": self.update_if,
            "3": self.update_rankings,
            "4": self.update_ppv,
            "5": self.add_trendmd_widget,
            "6": self.quit
        }
    
    
    def create_file_structure(self):
        # used to store a back-up of the original config.xml
        try:
            mkdir(join(self.current_dir, 'original'))
        except Exception as e:
            pass
                     
        # used as the location for modified config.xml ready to upload
        try:
            mkdir(join(self.current_dir, 'new'))
        except Exception as e:
            pass

        # Path to data spreadsheet to populate widgets to be made
        try:
            mkdir(join(self.current_dir, 'data'))
        except Exception as e:
            pass
    
    def display_menu(self):        
        if exists(join(self.current_dir, "sitebuilder_secrets.py")):
            print('''
            
            Sitebuilder Interactions Menu
            
            1. Create ACLs
            2. Update Impact Factor
            3. Update Rankings
            4. Update PPV
            5. Add TrendMD widget
            6. Quit program            
            ''')
            
        else:
            print(f"Please create a 'secrets.py' file at {self.current_dir}")
            print('''
                
                
            This file should contain the following values: -
                
                username = "enter_your_sitebuilder_username"
                password = "enter_your_sibuilder_password"
                
            The format must adhere to what is displayed, i.e. the '=' and '""' must be retained,
            although the tabs should not be included.
                
                
            ''')
            input("Please press enter to clear this message and to exit the program: ")
            sys.exit(0)
            
    def run(self):
        self.create_file_structure()
                     
        while True:
            self.display_menu()
            
            choice = input("Please enter a numeric option: ")
            action = self.choices.get(choice)
            
            if action:
                action()
            
            else:
                print("\n\n")
                print(f"{choice} is not a valid choice.")
    
    @staticmethod
    def acl_creation():
        acl = AutomatedContentListings()
        acl.check_share_locations_exist()

        for file in listdir(acl.acl_requests_dir):
            acl.combine_acl_lists(file)

        acl.create_working_list_and_archive_dataframe(acl.combined_acl_requests_df)

        for journal in acl.combined_acl_requests_df['url_shortcode']:
            SitebuilderSite(journal, "config.xml")

        exception_list = []
        count = 0
        for journal in tqdm(SitebuilderSite.files_dict,
                          desc='Downloading XML files: ',
                          position=0, leave=True,
                          file = sys.stdout):
            exception_list, count = SitebuilderInteraction.get_data(SitebuilderSite.files_dict[journal], exception_list, count)

        for journal in tqdm(SitebuilderSite.files_dict,
                          desc='Modifying XML files: ',
                          position=0, leave=True,
                          file = sys.stdout):
    
            site = SitebuilderSite.files_dict[journal]
        
            tqdm.write(f"Modifying {site.journal_shortcode}")

            ModifyFile.add_top_level_widget_xml(site)
            ModifyFile.modify_xml(site)

        for journal in tqdm(SitebuilderSite.files_dict,
                          desc='Posting XML files to Sitebuilder: ',
                          position=0, leave=True,
                          file = sys.stdout):

            site = SitebuilderSite.files_dict[journal]

            try:
                count = 0
                while count < 5 & SitebuilderInteraction.post_xml(site) != 0:
                    count += 1

            except Exception as e:
                tqdm.write(f'Unable to post XML: {site.journal_shortcode}: {e}')

        for journal in tqdm(SitebuilderSite.files_dict,
                          desc='Publishing site to live: ',
                          position=0, leave=True,
                          file = sys.stdout):
            SitebuilderInteraction.publish_to_live(SitebuilderSite.files_dict[journal])
        
        acl_df = pd.read_excel(acl.acl_settings_xlsx)

        email_recipients = set()
        [email_recipients.add(x) for x in acl_df['UserEmail'] if "could not" not in x]

        email_string = ''

        for i, x in enumerate(email_recipients):
            if i < len(email_recipients) - 1:
                email_string += f'{x}; '
            else:
                email_string += x

        print(f"\nACLs have been created for the following users: - \n\n{email_string}"
              "\n\nEmail them to confirm the creation of their ACLs along with the Archive ACL spreadsheet for this run.")
        
        acl.delete_all_acls()
    
    @staticmethod
    def confirm_data_file_structure():
        print('''
        
        Please confirm that a file is in the "data" folder and that the structure is as follows with the exact column names for the relevant file: -
        
        if.csv
        url_shortcode    One year    Five year
        
        OR
        
        ranking.csv        
        url_shortcode    Ranking Category    Ranking
        
        OR
        
        ppv.csv
        url_shortcode    GBP    EUR    USD
        
        OR
        
        trendmd.csv
        url_shortcode    id
        
        
        For "if.csv", null values for One year and Five year MUST be empty fields.
        
        For "ppv.csv" the url_shortcode should be confirmed to be the correct codes, i.e. not production codes.
        
        If anything is not correct please press "q", followed by enter, to exit or press the enter key to continue.
        
        ''')
    
    def update_if(self):
        while True:
            self.confirm_data_file_structure()
            
            if input("Press \"q\" followed by enter to exit or any key to continue") != "q":
                count = 0
                exception_list = []
                if_df = pd.read_csv(join(self.current_dir, "data", "if.csv"))
                no_na_if_df = if_df.fillna(0)
                
                for journal in tqdm(no_na_if_df['url_shortcode'],
                                  desc='Downloading XML files: ',
                                  position=0, leave=True,
                                  file = sys.stdout):

                    new_site = SitebuilderSite(journal, "data.xml")
                    exception_list, count = SitebuilderInteraction.get_data(new_site, exception_list, count)

                for journal in tqdm(SitebuilderSite.files_dict,
                                  desc='Modifying XML files: ',
                                  position=0, leave=True,
                                  file = sys.stdout):
                    
                    site = SitebuilderSite.files_dict[journal]
                    

                    one_year = no_na_if_df[no_na_if_df['url_shortcode'] == site.journal_shortcode]['One year'].values
                    five_year = no_na_if_df[no_na_if_df['url_shortcode'] == site.journal_shortcode]['Five year'].values

                    
                    ModifyFile.update_current_years_if(site, one_year[0], five_year[0])

                for journal in tqdm(SitebuilderSite.files_dict,
                                  desc='Posting XML files to Sitebuilder: ',
                                  position=0, leave=True,
                                  file = sys.stdout):

                    site = SitebuilderSite.files_dict[journal]

                    try:
                        count = 0
                        while count < 5 & SitebuilderInteraction.post_xml(site) != 0:
                            count += 1

                    except Exception as e:
                        tqdm.write(f'Unable to post XML: {site.journal_shortcode}: {e}')
            
            else:
                self.quit()
            
            break
    
    def update_rankings(self):
        while True:
            self.confirm_data_file_structure()
            
            if input("Press \"q\" followed by enter to exit or any key to continue") != "q":
                count = 0
                exception_list = []
                
                rankings_df = pd.read_csv(join(self.current_dir, "data", "rankings.csv"))
                
                journal_shortcodes = []
                [journal_shortcodes.append(x) for x in rankings_df['url_shortcode'] if x not in journal_shortcodes]
                
                for journal in tqdm(journal_shortcodes,
                                  desc='Downloading XML files: ',
                                  position=0, leave=True,
                                  file = sys.stdout):

                    new_site = SitebuilderSite(journal, "rankings.txt")
                    exception_list, count = SitebuilderInteraction.get_data(new_site, exception_list, count)

                for i in trange(len(rankings_df['url_shortcode']),
                                  desc='Modifying XML files: ',
                                  position=0, leave=True,
                                  file = sys.stdout):
                    
                    site = SitebuilderSite.files_dict[rankings_df.iloc[i]['url_shortcode']]
                    
                    ranking_name = rankings_df.iloc[i]['Ranking Category']
                    rank = rankings_df.iloc[i]['Ranking']

                    
                    ModifyFile.update_current_years_ranking(site, ranking_name, rank)

                for journal in tqdm(SitebuilderSite.files_dict,
                                  desc='Posting XML files to Sitebuilder: ',
                                  position=0, leave=True,
                                  file = sys.stdout):

                    site = SitebuilderSite.files_dict[journal]

                    try:
                        count = 0
                        while count < 5 & SitebuilderInteraction.post_xml(site) != 0:
                            count += 1

                    except Exception as e:
                        tqdm.write(f'Unable to post XML: {site.journal_shortcode}: {e}')
            
            else:
                self.quit()
            
            break
    
    def update_ppv():
        while True:
            self.confirm_data_file_structure()
            
            if input("Press \"q\" followed by enter to exit or any key to continue") != "q":
                count = 0
                exception_list = []
                
                ppv_df = pd.read_csv(join(self.current_dir, "data", "ppv.csv"))
                
                journal_shortcodes = []
                [journal_shortcodes.append(x) for x in ppv_df['url_shortcode'] if x not in journal_shortcodes]
                
                for journal in tqdm(journal_shortcodes,
                                  desc='Downloading XML files: ',
                                  position=0, leave=True,
                                  file = sys.stdout):

                    new_site = SitebuilderSite(journal, "data.xml")
                    exception_list, count = SitebuilderInteraction.get_data(new_site, exception_list, count)

                for i in trange(len(ppv_df['url_shortcode']),
                                  desc='Modifying XML files: ',
                                  position=0, leave=True,
                                  file = sys.stdout):
                    
                    site = SitebuilderSite.files_dict[ppv_df.iloc[i]['url_shortcode']]
                    
                    ModifyFile.update_ppv(site, ppv_df)

                for journal in tqdm(SitebuilderSite.files_dict,
                                  desc='Posting XML files to Sitebuilder: ',
                                  position=0, leave=True,
                                  file = sys.stdout):

                    site = SitebuilderSite.files_dict[journal]

                    try:
                        count = 0
                        while count < 5 & SitebuilderInteraction.post_xml(site) != 0:
                            count += 1

                    except Exception as e:
                        tqdm.write(f'Unable to post XML: {site.journal_shortcode}: {e}')
            
            else:
                self.quit()
            
            break
    
    def add_trendmd_widget(self):
        while True:
            self.confirm_data_file_structure()
            
            if input("Press \"q\" followed by enter to exit or any key to continue") != "q":
                count = 0
                exception_list = []
                
                trendmd_df = pd.read_csv(join(self.current_dir, "data", "trendmd.csv"))
                
                journal_shortcodes = []
                [journal_shortcodes.append(x) for x in ppv_df['url_shortcode'] if x not in journal_shortcodes]
                
                for journal in tqdm(journal_shortcodes,
                                  desc='Downloading XML files: ',
                                  position=0, leave=True,
                                  file = sys.stdout):

                    new_site = SitebuilderSite(journal, "data.xml")
                    exception_list, count = SitebuilderInteraction.get_data(new_site, exception_list, count)

                for i in trange(len(trendmd_df['url_shortcode']),
                                  desc='Modifying XML files: ',
                                  position=0, leave=True,
                                  file = sys.stdout):
                    
                    site = SitebuilderSite.files_dict[trendmd_df.iloc[i]['url_shortcode']]
                    
                    ModifyFile.update_ppv(site, trendmd_df[trendmd_df['url_shortcode'] == site.journal_shortcode]['id'])

                for journal in tqdm(SitebuilderSite.files_dict,
                                  desc='Posting XML files to Sitebuilder: ',
                                  position=0, leave=True,
                                  file = sys.stdout):

                    site = SitebuilderSite.files_dict[journal]

                    try:
                        count = 0
                        while count < 5 & SitebuilderInteraction.post_xml(site) != 0:
                            count += 1

                    except Exception as e:
                        tqdm.write(f'Unable to post XML: {site.journal_shortcode}: {e}')
            
            else:
                self.quit()
            
            break
    
    @staticmethod
    def quit():
        sys.exit(0)
