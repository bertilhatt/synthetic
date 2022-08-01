import datetime as dt
import pandas as pd
from random import random, randint, choices, weibullvariate


class Sample():
    def __init__(self, n_users, start, stop, site_name, cols): 
        self.n_users = n_users
        self.start = dt.datetime.combine(start, dt.time(0, 0, 0))
        self.stop = dt.datetime.combine(stop, dt.time(0, 0, 0))
        self.duration = (self.stop-self.start).total_seconds()
        self.site_name = site_name
        self.cols = cols
        self.output = pd.DataFrame(columns=cols)

    def later(self, visit):
        return visit + (self.stop - visit) * random()

    def advance(self, visit):
        return (visit-self.start).total_seconds() / self.duration
    
    def loop(self, churn, explore_rate, conversion_rate, shift_rate, confirmation_rate):
        for i in range(self.n_users):
            if i % 1000 == 0:
                print('Generating user', i, '/', self.n_users)
            domain = choices(
                ['co.uk', 'de', 'fr', 'it', 'sp', 'se', 'dk','no'],
                weights=[.34, .35, .11, .09, .05, .02, .02, .02],
            )[0]
            session = Session(i, domain, self.start, self.cols, self.site_name)
            advance = self.advance(session.visit)
            while random() > churn / (1.001-advance):
                # TODO: tunr churn rate into a function
                session.visit = self.later(session.visit)
                advance = self.advance(session.visit)
                platform = choices(
                    ['mobile', 'www'],
                    weights=[.2+.6*advance, .8-.6*advance],
                )[0]
                self.output = self.output.append(session.log_page(platform, 'home'))

                deal = randint(0, 1000)
                while random() < explore_rate:
                    session.wait()
                    deal = randint(0, 1000)
                    self.output = self.output.append(
                        session.log_page(platform, 'deal', deal))
            
                if random() < conversion_rate[platform] + advance*shift_rate:
                    # TODO: tunr conversion rate into a function
                    session.wait()
                    transaction = randint(100_000, 1000_000)
                    self.output = self.output.append(
                        session.log_page(platform, 'payment', deal, transaction))

                    if random() < confirmation_rate:
                        session.wait()
                        self.output = self.output.append(
                            session.log_page(platform, 'confirm', deal, transaction))
                    # TODO: Add more attempte at payments


class Session():
    def __init__(
        self,
        i: str,
        # platform: str,
        domain: str,
        visit: dt.datetime,
        cols: list[str],
        site_name: str,
    ):
        self.i = i
        # self.platform = platform
        self.domain = domain
        self.visit = visit
        self.cols = cols
        self.site_name = site_name
    
    def wait(self):
        self.visit += dt.timedelta(seconds=weibullvariate(10, 2)) 

    def log_page(
        self,
        platform: str,
        step: str,
        deal: int = None,
        transaction: int = None,
    ):
        site = '.'.join([platform, self.site_name, self.domain])
        elements = [site, step]
        if deal:
            elements += [str(deal)]
        url = '/'.join(elements)
        info = [self.visit, self.i, url, step, platform, self.domain, deal, transaction]
        return pd.DataFrame([info], columns=self.cols)


def generate_sessions(n_users: int, start: dt.date, stop: dt.date, churn: float = 0.2):
    cols = ['timestamp', 'user_id', 'url', 'page_type', 'platform', 'domain', 'deal', 'transaction']
    site_name = 'examplesite'
    sample = Sample(n_users, start, stop, site_name, cols)

    # Mix marketing effect
    explore_rate = .6
    conversion_rate = {'mobile': .16, 'www': .05}
    shift_rate = -.035
    confirmation_rate = .97

    sample.loop(churn, explore_rate, conversion_rate, shift_rate, confirmation_rate)    
    return sample.output.sort_values('timestamp').reindex()


if __name__ == '__main__':
    output = generate_sessions(18_000, dt.date(2020, 3, 1), dt.date(2021, 3, 1))
    output.to_csv('data/output_new.csv')

# TODO
# Pattern of session as transition graph
# Format of output as parameter
# Aggregate data into summaries