from os.path import abspath, join, exists, getctime
from os import getlogin
from os import remove
from os import listdir
import sys
from datetime import date
from time import gmtime

import pandas as pd
from tqdm import tqdm

class AutomatedContentListings:
    '''
    ACL combination and deletion.
    '''
    
    current_dir = abspath("")
    
    # Invidual widget request directory location user retrieved from system information
    teams_acl_root = f"C:/Users/{getlogin()}/<company name>/Automated ACL Requests - General"
    # Share folder locations
    acl_requests_dir = join(teams_acl_root, "ACL Requests")
    
    combined_acl_requests_df = pd.DataFrame()
    created_date_list = []
    
    dtypes = {
        'JournalNameEnabled': 'bool',
        'ArticleTypeEnabled': 'bool',
        'SeriesCategoryEnabled': 'bool',
        'ArticleTocHeadingEnabled': 'bool',
        'CitationEnabled': 'bool',
        'AuthorsEnabled': 'bool',
        'FeaturedFigureOrFirstImageEnabled': 'bool',
        'TeaserTextEnabled': 'bool',
        'Title.Enabled': 'bool',
        'PublicationDateEnabled': 'bool',
        'ContentTypeLabelEnabled': 'bool',
        'TeaserTextMaxCharacterLength': 'int64',
        'NumberOfResults': 'int64',
        'NumberOfColumns': 'int64',
        'ArticleListPageSize': 'int64',
        'NumYearsOfCitations': 'int64'
    }
    
    # Get today's date and put it into year_month_day format
    date = date.today()
    date_y_m_d = date.strftime("%y_%m_%d")

    acl_settings_xlsx = join(current_dir, 'data', 'acl_config_settings.xlsx')
    acl_archive_file = join(teams_acl_root, "Archive", f"{date_y_m_d}_acl_config_settings.xlsx")
    
    deletion_list = list()
    
    def check_share_locations_exist(self):
        '''
        Terminate program if user has not set up the share folders.
        '''
        if exists(self.teams_acl_root) is False:
            tqdm.write(f'No such filepath: - {self.teams_acl_root}\n\nPlease confirm that you have added the Sharepoint location.')
            input('Press the "enter" key to clear this message and exit.')
            sys.exit(0)
    
    @classmethod
    def combine_acl_lists(cls, file: str):
        '''
        Take the individual, single line, ACL requests and combine them into one dataframe.
        
        If there are any erroneous UTF-8 characters open with different encoding to replace
        the offending characters.
        '''
        
        individual_request_location = join(cls.acl_requests_dir, file)
        cls.deletion_list.append(individual_request_location)
        
        tqdm.write(individual_request_location)

        try:
            acl_settings_df = pd.read_csv(individual_request_location)
        except Exception as e:
            print(e)
            acl_settings_df = pd.read_csv(individual_request_location, encoding = "ISO-8859-1")
            acl_settings_df['AdvancedQuery'][0] = acl_settings_df['AdvancedQuery'][0].replace('\x93', '"').replace('\x94', '"')

        acl_settings_df.dropna(axis=0, how='all', inplace=True)

        try:
            acl_settings_df.rename(columns={'TitleText':'Title.Text','TitleEnabled':'Title.Enabled'}, inplace=True)
        except:
            pass

        cls.combined_acl_requests_df = cls.combined_acl_requests_df.append(acl_settings_df)

        created_date = gmtime(getctime(individual_request_location))
        d_m_y = f'{created_date[2]}/{created_date[1]}/{created_date[0]}'
        for i in range(len(acl_settings_df)):
            cls.created_date_list.append(d_m_y)
    
    def create_working_list_and_archive_dataframe(self, combined_dataframe):
        '''
        Create excel spreadsheets to store as archive, for future reference, and as the file to
        work from whilst adding the new ACL settings.
        '''
        
        try:
            # Dictionary comprehension to remove any dtype changes whose
            # column does not exist in the df
            {self.dtypes.pop(k) for k in list(self.dtypes) if k not in combined_dataframe.columns}

            combined_dataframe[list(self.dtypes.keys())] = combined_dataframe[self.dtypes.keys()].fillna(0)
            combined_dataframe = combined_dataframe.astype(self.dtypes)

            combined_acl_requests_no_nan = combined_dataframe[~combined_dataframe['url_shortcode'].isna()]

            # Note change occurences of acl_settings_xlsx for combined_acl_requests df
            # and then remove this save
            combined_acl_requests_no_nan.to_excel(self.acl_settings_xlsx, index=False)

            # Create a new column in the archive of the date list
            # to use for tracking purposes
            combined_dataframe['created_date'] = self.created_date_list

            # Save a copy of the combined dataframe to an archive
            combined_dataframe.to_excel(self.acl_archive_file, index=False)
        except Exception as e:
            tqdm.write(e)
        
    @classmethod
    def delete_all_acls(cls):
        '''
        Function to delete all requests from the active working directory.
        
        ---WARNING---
        Only run after all code has completed succesfully to ensure nothing is removed too soon.
        '''
        for x in listdir(cls.acl_requests_dir):
            request_location = join(cls.acl_requests_dir, x)
            
            if request_location in cls.deletion_list:
                remove(request_location)
