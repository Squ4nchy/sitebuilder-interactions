import re

import requests
from tqdm import tqdm
from bs4 import BeautifulSoup as bs

from sitebuilder_secrets import username, password
from sitebuilder_interaction_tasks.SitebuilderSite import SitebuilderSite

class SitebuilderInteraction(SitebuilderSite):
    '''
    Sitebuilder interactions such as downloading file, uploading, etc.
    '''
    
    login_creds = {'Username': username, 'Password': password}
    
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,"
        "*/*;q=0.8,application/signed-exchange;v=b3",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
        "Dnt": "1",
        "Host": "sitebuilder.academic.oup.com",
        "Origin": "<sitebuilder root>",
        "Referer": "<sitebuilder root>/sign-in?returnUrl=%2f",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko"
        ") Chrome/79.0.3945.130 Safari/537.36"
    }
    
    @classmethod
    def get_session(cls):
        s = requests.session()
        s.headers.update(cls.headers)
        s.post(f'{cls.sitebuilder_root}/sign-in', data=cls.login_creds)
        
        return s
    
    @staticmethod
    def get_data(site: SitebuilderSite, exception_list, count):

        http_session = SitebuilderInteraction.get_session()
        
        count += 1

        tqdm.write(f"{count}: {site.journal_shortcode}")

        html = http_session.get(site.site_url)
        soup = bs(html.content, 'html.parser')

        if site.file_extension == "data.xml":
            p = re.compile(r"SiteDataCore&workflowSubType=$")

            for x in soup.find_all(attrs={"class": "btn-action"}, text="Download"):
                href = x.get("href")
                match = re.findall(p, x.get("href"))
                if match:
                    file_url_stub = href

        elif site.file_extension != "config.xml":
            for x in soup.find_all(attrs={"class": "btn-action"}, text="Download"):
                href = x.get("href")
                if site.file_type_sb_url_conversion[site.file_extension] in href:
                    file_url_stub = href

        else:
            for x in soup.find_all(attrs={"class": "btn-action"}, text="Download"):
                href = x.get("href")
                if all(y in x.get('href') for y in ['Live', 'SiteCore']):
                    file_url_stub = href
        
        try:
            file_site_location = site.sitebuilder_root + file_url_stub
            file_contents = http_session.get(file_site_location)
            text = file_contents.text
            
            # Site builder was giving XML that contained random characters which
            # was stopping the XML parser from reading the file as it did not begin
            # with "<"
            while text[0] != "<":
                text = text[1:]
                        
        except Exception as e:
            tqdm.write(str(e))
            tqdm.write(f"\n{site.journal_shortcode} could not be found")
            exception_list.append(site.journal_shortcode)
            
            return(exception_list, count)


        with open(site.original_file_path, "w+", encoding="utf-8") as f:
            f.write(text)
            f.close()

        return(exception_list, count)
    
    @classmethod
    def post_xml(cls, site: SitebuilderSite):

        http_session = cls.get_session()
        
        file_name = f"{site.journal_shortcode}_{site.file_extension}"
        
        file_to_upload = {file_name: open(site.new_file_path, 'rb')}

        html = http_session.get(site.site_url)
        html_soup = bs(html.content, 'html.parser')
        
        for x in html_soup.find_all("input", attrs={"class": "btn-action btn-primary"}):
            if file_name in x.get("data-url"):
                upload_location = x.get("data-url")
        
        tqdm.write(f"{site.journal_shortcode}: Uploading to - {site.sitebuilder_root}{upload_location}")

        try:
            upload_xml = http_session.post(f"{site.sitebuilder_root}{upload_location}", files=file_to_upload, timeout=240)
            upload_soup = bs(upload_xml.content, 'html.parser')
            tqdm.write(f"{site.journal_shortcode}: {upload_soup}\n")
            return 0
        except Exception as e:
            tqdm.write(f"{site.journal_shortcode} could not be found: {e}\n")
            return 1
        
    @classmethod
    def publish_to_live(cls, site: SitebuilderSite):
        http_session = cls.get_session()

        html = http_session.get(site.site_url)
        soup = bs(html.content, 'html.parser')
        
        for x in soup.find_all(class_='btn-warning is-active'):
            publish_site_stub = x.get('data-url')

        try:
            publish_page = http_session.post(f"{site.sitebuilder_root}{publish_site_stub}")
            soup = bs(publish_page.content, 'html.parser')
            tqdm.write(f'{site.journal_shortcode}: {soup.prettify()}')
            return 0
        except Exception as e:
            tqdm.write(str(e))
            return 1

        time_to_wait = 3
        
        tqdm.write(f'{site.journal_shortcode} published, waiting {time_to_wait} seconds to complete.')

        time.sleep(time_to_wait)
