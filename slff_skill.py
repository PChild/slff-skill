from scoring.slff import ScoreSLFF
import trueskill
import pandas



results_url_base = "https://docs.google.com/spreadsheets/d/%s/export?gid=%s&format=csv"  # (key, sheet)

results_2019_key = "1-2Flli3g1d_r2sEkr0DjLnyXGgyn3LwC3uSh5uVThTc"
results_2019_sheet = "963745347"
results_2019_url = results_url_base % (results_2019_key, results_2019_sheet)

teams_2019 = ["FLCN", "1.21 GW", "QD", "TBC", "TLC", "CHS", "SS", "MB",
              "QwEST", "JSM", "FC", "FP", "TGA", "TSIMFD", "TDC", "LM"]

draft_results = pandas.read_csv(results_2019_url, header=0, skiprows=1)

normal_season = draft_results[pandas.notnull(draft_results['Tier'])]
normal_season['full_code'] = normal_season['event code'] + normal_season['Tier'].astype(int).astype(str)
event_keys = normal_season['full_code'].unique()
print(event_keys)
