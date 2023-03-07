from sitebuilder_interaction_tasks.FileToUpdate import FileToUpdate

class SitebuilderSite(FileToUpdate):
    
    '''
    Specify Sitebuilder site locations and file type to url conversions.
    '''
    sitebuilder_root = "<sitebuilder root>"
    
    file_type_sb_url_conversion = {
        'config.xml': 'SiteCore',
        'data.xml': 'SiteDataCore',
        'subs_pricing.txt': 'SiteDataCoreSubscriptionPricing',
        'rankings.txt': 'SiteDataCoreRankings'
    }
    
    def __init__(self, journal_shortcode, file_extension):
        super().__init__(journal_shortcode, file_extension)
        
        if self.journal_shortcode == "umbrella":
            self.site_url = f"{self.sitebuilder_root}/edit-site?publishingid=f60a5800-41b4-48a1-8cb9-8aafe7624b45"
        else:
            self.site_url = f"{self.sitebuilder_root}/edit-site?urlprefix={self.journal_shortcode}"
