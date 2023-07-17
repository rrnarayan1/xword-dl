from .newyorktimesdownloader import NewYorkTimesDownloader


class NewYorkTimesMiniDownloader(NewYorkTimesDownloader):
    command = 'nytm'
    outlet = 'New York Times Mini'
    outlet_prefix = 'NY Times Mini'

    def __init__(self, **kwargs):
        BaseDownloader.__init__(self, **kwargs)
        self.headers = {}
        self.cookies = {}

    @staticmethod
    def matches_url(url_components):
        return ('nytimes.com' in url_components.netloc
                    and 'mini' in url_components.path)

    def find_latest(self):
        return 'https://www.nytimes.com/svc/crosswords/v6/puzzle/mini.json'

    def find_solver(self, url):
        return 'https://www.nytimes.com/svc/crosswords/v6/puzzle/mini.json'

    def parse_xword(self, xword_data):
        try:
            self.date = datetime.datetime.strptime(xword_data["publicationDate"], '%Y-%m-%d')
            #print(xword_data)
            return super().parse_xword(xword_data)
        except ValueError:
            raise XWordDLException('Encountered error while parsing data. Maybe the selected puzzle is not a crossword?')