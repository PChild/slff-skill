import trueskill
import pandas
import csv


def update_ratings_log(tm_rtngs, event, cnt):
    d = {tm: trueskill.expose(rtng) for (tm, rtng) in tm_rtngs.items()}
    d['event'] = event
    d['cnt'] = cnt
    return d


if __name__ == '__main__':
    non_part_change = 1.0  # TODO test this value / read more
    remote = False

    if remote:
        results_url_base = 'https://docs.google.com/spreadsheets/d/%s/export?gid=%s&format=csv'  # (key, sheet)
        results_key = '1X8VZQInqpF2OdIE1X6IYKApZC6b3vBCtjMcBuEMAukY'
        results_sheet = '0'
        results_url = results_url_base % (results_key, results_sheet)
        off_df = pandas.read_csv(results_url, header=0)
    else:
        off_df = pandas.read_csv('off_results_2019.csv', header=0)

    off_df['Tiered Code'] = off_df['Event Code'] + off_df['Tier'].astype(str)
    off_df['Player'] = off_df['Player'].str.lower()
    off_players = list(off_df['Player'].unique())
    off_events = list(off_df['Tiered Code'].unique())

    ratings_log = {}
    player_ratings = {}
    idx = 0
    for player in off_players:
        player_ratings[player] = trueskill.Rating()
    ratings_log['initial'] = update_ratings_log(player_ratings, 'initial', idx)
    idx += 1

    for event in list(off_df['Event Code'].unique()):
        tiers = list(off_df[off_df['Event Code'] == event]['Tier'].unique())
        participants = list(off_df[off_df['Event Code'] == event]['Player'].unique())

        for player in off_players:
            if player not in participants:
                player_skill = player_ratings[player]
                player_ratings[player] = trueskill.Rating(player_skill.mu, player_skill.sigma + non_part_change)
        ratings_log[event + '_np'] = update_ratings_log(player_ratings, event + '_np', idx)
        idx += 1


        for tier in tiers:
            tier_code = event + str(tier)
            tier_data = off_df[off_df['Tiered Code'] == tier_code].sort_values(by='Eff', ascending=False)

            tier_ratings = []
            for player in tier_data['Player']:
                tier_ratings.append((player_ratings[player], ))
            tier_ratings = trueskill.rate(tier_ratings)

            for cnt, new_rating in enumerate(tier_ratings):
                player = tier_data['Player'].iloc[cnt]
                player_ratings[player] = new_rating[0]

            ratings_log[tier_code] = update_ratings_log(player_ratings, tier_code, idx)
            idx += 1

    with open('off_skill_2019.csv', 'w', newline='') as outfile:
        fieldnames = ['cnt', 'event'] + list(player_ratings.keys())
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for entry in ratings_log.keys():
            writer.writerow(ratings_log[entry])
    outfile.close()
