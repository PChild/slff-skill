import trueskill
import pandas
import csv


def update_ratings_log(tm_rtngs, event, cnt):
    d = {tm: trueskill.expose(rtng) for (tm, rtng) in tm_rtngs.items()}
    d['event'] = event
    d['cnt'] = cnt
    return d


if __name__ == '__main__':
    results_url_base = 'https://docs.google.com/spreadsheets/d/%s/export?gid=%s&format=csv'  # (key, sheet)
    results_key = '1X8VZQInqpF2OdIE1X6IYKApZC6b3vBCtjMcBuEMAukY'
    results_sheet = '0'
    results_url = results_url_base % (results_key, results_sheet)
    off_df = pandas.read_csv(results_url, header=0)
    off_df['Tiered Code'] = off_df['Event Code'] + off_df['Tier'].astype(str)

    off_players = list(off_df['Player'].unique())
    off_events = list(off_df['Tiered Code'].unique())

    ratings_log = {}
    player_ratings = {}
    for player in off_players:
        player_ratings[player] = trueskill.Rating()
    ratings_log['initial'] = update_ratings_log(player_ratings, 'initial', 0)

    for cnt, event in enumerate(off_events):
        print("Processing", event)
        event_results = off_df[off_df['Tiered Code'] == event].sort_values(by='Eff', ascending=False)
        ratings = []
        for player in event_results['Player']:
            ratings.append((player_ratings[player],))
        ratings = trueskill.rate(ratings)
        for idx, rating in enumerate(ratings):
            team = event_results['Player'].iloc[idx]
            player_ratings[team] = rating[0]
        ratings_log[event] = update_ratings_log(player_ratings, event, cnt + 1)

    with open('off_skill_2019.csv', 'w', newline='') as outfile:
        fieldnames = ['cnt', 'event'] + list(player_ratings.keys())
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for entry in ratings_log.keys():
            writer.writerow(ratings_log[entry])
    outfile.close()
