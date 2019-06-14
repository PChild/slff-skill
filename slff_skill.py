from pandas.api.types import is_numeric_dtype
from scoring.slff import ScoreSLFF
import trueskill
import pandas
import csv


class DraftData:
    def __init__(self, key, sheet, skip_rows=0):
        self.results_url_base = 'https://docs.google.com/spreadsheets/d/%s/export?gid=%s&format=csv'  # (key, sheet)
        self.results_key = key
        self.results_sheet = sheet
        self.results_url = self.results_url_base % (self.results_key, self.results_sheet)
        self.skip_rows = skip_rows
        self.season_df = pandas.read_csv(self.results_url, header=0, skiprows=skip_rows)
        self.normal_season = self.get_normal_season()
        self.tiered_keys = list(self.normal_season['Tiered Code'].unique())
        self.slff_players = list(self.normal_season['Player'].unique())
        self.scorer = ScoreSLFF()

    def get_normal_season(self):
        normal_season = self.season_df[pandas.notnull(self.season_df['Tier'])]

        # Ignoring chained assignment here and then turning it back on.
        pandas.options.mode.chained_assignment = None
        normal_season['Tiered Code'] = normal_season['event code'] + normal_season['Tier'].astype(int).astype(str)
        pandas.options.mode.chained_assignment = 'warn'
        return normal_season

    def get_season_draft(self, tiered_key):
        draft_df = self.normal_season[self.normal_season['Tiered Code'] == tiered_key]

        pandas.options.mode.chained_assignment = None
        draft_df.dropna(axis='columns', inplace=True)

        for col in draft_df.columns:
            if is_numeric_dtype(draft_df[col]):
                draft_df[col] = draft_df[col].astype(int)
        pandas.options.mode.chained_assignment = 'warn'

        # All events will have a tiered code and player, add appropriate rounds per event
        col_list = ['Tiered Code', 'Player']
        for col in draft_df.columns:
            if 'Round' in col:
                col_list.append(col)

        draft_df = draft_df[col_list]

        return draft_df

    def score_draft(self, tiered_key):
        plain_key = tiered_key[:-1]
        non_district = '2019' in plain_key

        if non_district:
            scores_dict = self.scorer.score_event(plain_key)
            event_draft = self.get_season_draft(tiered_key)
            event_draft['Total'] = 0

            round_count = len([item for item in event_draft.columns if 'Round' in item])

            # This is bad and stupid but doing it differently is hard
            for rnd in range(1, round_count + 1):
                col_data = []
                for idx, row in event_draft.iterrows():
                    round_key = 'Round ' + str(rnd)
                    team_key = 'frc' + str(row[round_key])
                    team_points = 0
                    if team_key in scores_dict:
                        team_points = scores_dict[team_key]['total']
                    col_data.append(team_points)
                event_draft['Points ' + str(rnd)] = col_data
                event_draft['Total'] += event_draft['Points ' + str(rnd)]
            return event_draft
        return "districts bad"


def update_ratings_log(tm_rtngs, event, cnt):
    d = {tm: trueskill.expose(rtng) for (tm, rtng) in tm_rtngs.items()}
    d['event'] = event
    d['cnt'] = cnt
    return d


if __name__ == '__main__':
    key_2019 = '1-2Flli3g1d_r2sEkr0DjLnyXGgyn3LwC3uSh5uVThTc'
    sheet_2019 = '963745347'
    skips_2019 = 1

    slff_2019 = DraftData(key_2019, sheet_2019, skips_2019)

    # Initialize all SLFF teams in a dict with default ratings. Ratings log tracks exposed team ratings, team ratings
    # stores the actual current ratings objects for each of the teams.
    ratings_log = {}
    team_ratings = {}
    for team in slff_2019.slff_players:
        team_ratings[team] = trueskill.Rating()
    ratings_log['initial'] = update_ratings_log(team_ratings, 'initial', 0)

    events = slff_2019.tiered_keys
    bad_no_good = ['2019micmp1', '2019oncmp1']
    for cnt, event in enumerate(events):
        if '2019' in event and event not in bad_no_good:
            print("Processing", event)
            event_results = slff_2019.score_draft(event).sort_values(by='Total', ascending=False)
            ratings = []
            for player in event_results['Player']:
                ratings.append((team_ratings[player],))
            ratings = trueskill.rate(ratings)
            for idx, rating in enumerate(ratings):
                team = event_results['Player'].iloc[idx]
                team_ratings[team] = rating[0]
            ratings_log[event] = update_ratings_log(team_ratings, event, cnt + 1)

    with open('slff_skill_2019.csv', 'w', newline='') as outfile:
        fieldnames = ['cnt', 'event'] + list(team_ratings.keys())
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for entry in ratings_log.keys():
            writer.writerow(ratings_log[entry])
    outfile.close()
