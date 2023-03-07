from os.path import getmtime, getctime, exists
from datetime import datetime
from time import sleep

from lxml import etree as et
from tqdm import tqdm
import pandas as pd
import numpy as np

from sitebuilder_interaction_tasks.SitebuilderSite import SitebuilderSite
from sitebuilder_interaction_tasks.AutomatedContentListings import AutomatedContentListings

class ModifyFile:
    '''
    All functions to modify config, data, subscription pricing, and rankings file.
    
    This includes IF/Rankings, PPV, ACL requests, and TrendMD widget creation.
    '''
    
    @staticmethod
    def time_since_last_file_modification(file: str):
        file_last_modification_epoch = getmtime(file)
        file_last_modification = datetime.fromtimestamp(file_last_modification_epoch)
        time_since_last_modification = datetime.now() - file_last_modification
        
        return time_since_last_modification.seconds
    
    @classmethod
    def update_from_original_or_new(cls, site: SitebuilderSite):
        if exists(site.new_file_path) and cls.time_since_last_file_modification(site.new_file_path) < 60:
            return site.new_file_path

        else:
            return site.original_file_path
    
    @classmethod
    def add_top_level_widget_xml(cls, site: SitebuilderSite):
        '''
        Add the top level settings that are required for adding widget locations to.
        
        -Note-
        This method is rarely invoked.
        '''
        file_path = cls.update_from_original_or_new(site)
        tree = et.parse(file_path)           
        root = tree.getroot()

        block_settings = root.xpath('//Location[@name="MainContent"]/Block')
        single_page = root.xpath('//Page[@name="Home"]')
        page_settings = root.xpath('//PageSettings')
        site_template = root.xpath('//SiteTemplateSettings')

        if len(page_settings) == 0:
            settings = et.Element('PageSettings')
            page = et.SubElement(settings, 'Page', attrib={'name': 'Home'})
            location = et.SubElement(page, 'Location', attrib={'name': 'MainContent'})
            et.SubElement(location, 'Block')
            site_template_parent = site_template[0].getparent()
            site_template_parent.insert(site_template_parent.index(site_template[0])+1,
                                 settings)
            tree.write(site.new_file_path)

        elif len(single_page) == 0:
            page = et.Element('Page', attrib={'name': 'Home'})
            location = et.SubElement(page, 'Location', attrib={'name': 'MainContent'})
            et.SubElement(location, 'Block')
            page_settings[0].insert(0, page)
            tree.write(site.new_file_path)

        elif len(block_settings) == 0:
            location = et.Element('Location', attrib={'name': 'MainContent'})
            et.SubElement(location, 'Block')
            single_page[0].insert(0, location)
            tree.write(site.new_file_path)
    
    @classmethod
    def modify_xml(cls, site: SitebuilderSite):
        '''
        Convert the combined ACL requests list into a dictionary and create Magic/ALNP widget depending
        on which settings have been specified.
        '''
        
        # For each line in acl_settings_xlsx create a dictionary
        for d in pd.read_excel(AutomatedContentListings.acl_settings_xlsx).replace([np.nan], [None]).to_dict('records'):
            if d.pop('url_shortcode') != site.journal_shortcode:
                pass
            else:

                # The instance name is used to name the widget
                instance_name = d.pop('instance_name')

                try:
                    d.pop('UserEmail')
                except Exception as e:
                    pass

                try:
                    d.pop('TimeRequested')
                except Exception as e:
                    pass

                file_path = cls.update_from_original_or_new(site)
                tree = et.parse(file_path)

                root = tree.getroot()

                # Location of the element to add, change, or remove
                block = root.xpath('//Location[@name="MainContent"]/Block')
                settings = root.xpath('//WidgetSettings')

                try:
                    if d['Mode'] in ('MostRead', 'MostCited') or d['CombinedModeList'] is not None:
                        widget_block, widget_settings = cls.alnp_widget(d, instance_name)
                    else:
                        widget_block, widget_settings = cls.magic_widget(d, instance_name)

                    success_flag = True

                except:
                    success_flag = False
                    pass

                finally:
                    if success_flag is False:
                        widget_block, widget_settings = cls.magic_widget(d, instance_name)

                # Insert the XML elements, including subelements, into the correct
                # place in the existing XML file
                try:
                    block[0].insert(0, widget_block)

                except Exception as e:
                    tqdm.write(f'{site.journal_shortcode} - Tried to modify block 1:', str(e))

                settings[0].insert(0, widget_settings)

                # Write the new Tree to file
                tree.write(site.new_file_path)
                tqdm.write(f"{site.journal_shortcode} has been modified")
            
    @staticmethod
    def magic_widget(d, instance_name):
        '''
        Create magic widget based on settings dictionary.
        '''
        
        # Top level widget XML elements
        widget_block = et.Element('Widget', attrib={'type':'SelectableContentList',
                                                                      'instanceName':instance_name})

        widget_settings = et.Element('WidgetSetting', attrib={'type':'SelectableContentList',
                                                              'instanceName':instance_name,
                                                              'controllerName':'Solr'})
        # Use key/value pairs to build subelements of the
        # widget settings from acl_settings_xlsx         
        for k, v in d.items():
            # If the value is NaN skip the setting
            if pd.isnull(v):
                continue
            if k in ('Mode', 'ArticleListPageSize', 'NumYearsOfCitations'):
                continue
            else:
                k = str(k)
                v = str(v)

                if v in ('TRUE', 'FALSE', 'true', 'false'):
                    v = v.title()

                # XML encoding of values conflicts with ElementTree therefore
                # if '&quot;' or '&amp;' are apparent convert to standard
                if '&quot;' in v or '&amp;' in v:
                    v = v.replace('&quot;', '"').replace('&amp;', '&')
                    
                et.SubElement(widget_settings, 'Setting', attrib={'name':k,
                                                                  'value':v,
                                                                  'type':"RuntimeSetting"})

        # Hard coded widget settings
        et.SubElement(widget_settings, 'Setting', attrib={'name':'ShowBasicView',
                                                              'value':'True',
                                                              'type':"RuntimeSetting"})
        et.SubElement(widget_settings, 'Setting', attrib={'name':'VerticalListOrientation',
                                                              'value':'True',
                                                              'type':"RuntimeSetting"})
        et.SubElement(widget_settings, 'Setting', attrib={'name':'BrowseAllEnable',
                                                              'value':'False',
                                                              'type':"RuntimeSetting"})
        
        return(widget_block, widget_settings)
    
    @staticmethod
    def alnp_widget(d, instance_name):
        '''
        Create ALNP widget based on settings dictionary.
        '''

        if d['CombinedModeList'] != None:
            controller_name = 'OUPCache'
            action_name = 'ArticleListNewAndPopularCombinedView'
        else:
            controller_name = 'Article'
            action_name = 'ArticleListNewAndPopularByMode'

        # Top level widget XML elements
        widget_block = et.Element('Widget', attrib={'type':'ArticleListNewAndPopular',
                                                    'instanceName':instance_name})

        widget_settings = et.Element('WidgetSetting', attrib={'type':'ArticleListNewAndPopular',
                                                              'instanceName':instance_name,
                                                              'controllerName':controller_name,
                                                              'actionName': action_name})

        # Use key/value pairs to build subelements of the
        # widget settings from acl_settings_xlsx         
        for k, v in d.items():
            # If the value is NaN skip the setting
            if pd.isnull(v):
                continue
            # If the value is any variant of false, skip
            elif v in ('FALSE', 'False', 'false', False):
                continue
            else:
                k = str(k)
                v = str(v)

                if v in ('TRUE', 'FALSE', 'true', 'false'):
                    v = v.title()

                # XML encoding of values conflicts with  ElementTree therefore
                # if '&quot;' or '&amp;' are apparent convert to standard
                if '&quot;' in v or '&amp;' in v:
                    v = v.replace('&quot;', '"').replace('&amp;', '&')
                et.SubElement(widget_settings, 'Setting', attrib={'name':k,
                                                                  'value':v,
                                                                  'type':"RuntimeSetting"})

        return(widget_block, widget_settings)
    
    @classmethod
    def trendmd_widget(cls, site: SitebuilderSite, trendmd_id: str):
        '''
        Method to add TrendMD widgets.
        '''
        
        file_path = cls.update_from_original_or_new(site)
        tree = et.parse(file_path)
        root = tree.getroot()

        right_rail = root.xpath(".//*[@name='RightRail']/Block")
        widget_settings =  root.xpath(".//WidgetSettings")
        related_content = root.find(".//*[@type='RelatedContent']")
        related_pubmed = root.find(".//*[@type='RelatedPubMed']")
        trendmd_loc = root.find(".//Block/*[@type='TrendMD']")
        trendmd_settings = root.find(".//WidgetSettings/*[@type='TrendMD']")

        removal_list = [related_content, related_pubmed, trendmd_loc]

        for x in removal_list:
            try:
                x.getparent().remove(x)
            except Exception as e:
                tqdm.write(str(e))


        for x in iter(right_rail[1]):
            try:
                if x.attrib['type'] == 'SeeAlso':
                    pos = list(right_rail[1]).index(x)
                    pos += 1
                    
            except Exception as e:
                tqdm.write(f'{site.journal_shortcode}: {str(e)}')
                
                try:
                    if x.attrib['type'] == 'Alerts':
                        pos = list(right_rail[1]).index(x)
                        pos += 1
                        
                except Exception as e:
                    tqdm.write(f'{site.journal_shortcode}: {str(e)}')

        trendmd_block = et.Element('Widget', attrib={'type': 'TrendMD', 'instanceName': 'trendmd'})
        trendmd_settings = et.Element('WidgetSetting', attrib={'type': 'TrendMD', 'instanceName': 'trendmd', 'controllerName': 'ThirdParty'})
        et.SubElement(trendmd_settings, 'Setting', attrib={'name': 'Title.Enabled', 'value': 'false', 'type': 'RuntimeSetting'})
        et.SubElement(trendmd_settings, 'Setting', attrib={'name': 'TrendMdJournalId', 'value': f'{trendmd_id}', 'type': 'RuntimeSetting'})

        right_rail[1].insert(pos, trendmd_block)
        widget_settings[0].insert(0, trendmd_settings)

        tree.write(site.new_file_path)
    
    @classmethod
    def update_current_years_ranking(cls, site: SitebuilderSite, ranking_name, rank):
        
        file_path = cls.update_from_original_or_new(site)
        
        error_xml = True

        while error_xml is True:
            try:
                tree = et.parse(file_path)
                error_xml = False
                
            except et.XMLSyntaxError as e:
                tqdm.write(f"{site.journal_shortcode}: {e}")

                page = et.Element("category_rankings")
                et.SubElement(page, "category")
                tree = et.ElementTree(page)

                tree.write(file_path)
                sleep(2)
                
        root = tree.getroot()

        current_rank = root.xpath(f".//rank[@current='true']")
        ranking_name_location = root.xpath(f".//*[text()='{ranking_name}']")
        ranking_year = datetime.now().year - 1

        if len(current_rank) > 0:
            for ranking in current_rank:
                if ranking.attrib['year'] != str(ranking_year):
                    ranking.attrib['current'] = 'false'

        attributes = {
            "current": "true",
            "year": f"{ranking_year}"
        }

        new_ranking_element = et.Element("rank", attrib=attributes)
        new_ranking_element.text = f"{rank}"

        if len(ranking_name_location) == 0:
            top_level_category = et.Element('category', attrib={"display_on_homepage": "false"})
            name = et.SubElement(top_level_category, "name")
            name.text = ranking_name

            top_level_category.insert(1, new_ranking_element)

            root.insert(0, top_level_category)

        else:
            ranking_name_location[0].getparent().insert(1, new_ranking_element)


        tree.write(site.new_file_path)
        
    @classmethod
    def update_current_years_if(cls, site: SitebuilderSite, one_year, five_year):
        
        file_path = cls.update_from_original_or_new(site)
        tree = et.parse(file_path)
        root = tree.getroot()
        
        one_year = f"{float(one_year):.3f}"
        five_year = f"{float(five_year):.3f}"
        
        if_year = datetime.now().year - 1

        attributes = {
            "current": "true",
            "year": f"{if_year}"
        }
        
        current_if = root.xpath(f".//ImpactFactor[@current='true']")
        impact_factors = root.xpath(f".//ImpactFactors")
        
        if len(current_if) > 0:
            for impact_factor in current_if:
                if impact_factor.attrib['year'] != str(if_year):
                    impact_factor.attrib['current'] = 'false'

        new_if_element = et.Element("ImpactFactor", attrib=attributes)

        one_year_if_element = et.SubElement(new_if_element, "OneYear")
        one_year_if_element.text = one_year

        five_year_if_element = et.SubElement(new_if_element, "FiveYear")
        five_year_if_element.text = five_year
        
        if len(current_if) > 0:
            current_if[0].getparent().insert(0, new_if_element)
        else:
            impact_factors[0].insert(0, new_if_element)
        
        tree.write(site.new_file_path)
        
        @classmethod
        def update_ppv(cls, site: SitebuilderSite, ppv_df):
            
            ppv_period_year = datetime.now().year
            
            file_path = cls.update_from_original_or_new(site)
            tree = et.parse(file_path)
            root = tree.getroot()
            
            gbp_currency = ppv_df[ppv_df['url_shortcode'] == site.journal_shortcode]['GBP'].values[0]
            eur_currency = ppv_df[ppv_df['url_shortcode'] == site.journal_shortcode]['EUR'].values[0]
            usd_currency = ppv_df[ppv_df['url_shortcode'] == site.journal_shortcode]['USD'].values[0]
            
            try:    
                prices = root.find('.//Prices')
                price = ET.Element('Price', attrib={
                    'priceUsd': f'{float(usd_currency):.2f}',
                    'priceGbp': f'{float(gbp_currency):.2f}',
                    'priceEur': f'{float(eur_currency):.2f}',
                    'startDate': f'1/1/{ppv_period_year} 12:00:00 AM',
                    'endDate': f'12/31/{ppv_period_year} 11:59:59 PM'})
        
            except Exception as e:
                tqdm.write(f'{title}: {e}')
            
            prices.insert(len(prices),price)
            
            tree.write(site.new_file_path)