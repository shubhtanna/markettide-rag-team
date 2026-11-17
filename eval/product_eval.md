# Product evaluation (zero-hallucination pipeline)

- **questions**: 26
- **passed**: 24
- **behaviour correct**: 24
- **trap hits**: 0
- **fact check failures shown**: 0
- **judge claims supported**: 20/20
- **avg latency s**: 6.51

| id | type | question | expected | got | pass |
|---|---|---|---|---|---|
| f01 | factual | How much interim dividend did Ashok Leyland declare? | answered | answered (answered) | ✅ |
| f02 | factual (PDF only) | What order did Texmaco Rail receive and what is its value? | answered | answered (trimmed) | ✅ |
| f03 | factual (PDF only) | What is the buyback price per share announced by Zee Entertainment? | answered | answered (answered) | ✅ |
| f04 | factual (PDF only) | What is the capacity of the new Waaree Energies battery pack line? | answered | answered (answered) | ✅ |
| f05 | factual | What did Alembic Pharmaceuticals get USFDA approval for? | answered | answered (trimmed) | ✅ |
| f06 | factual | What did Reliance Industries announce this week? | answered | answered (repaired) | ✅ |
| f07 | factual | What is the record date for the Ashok Leyland dividend? | answered | answered (trimmed) | ✅ |
| l01 | list | Which companies announced a share buyback this week? | answered | declined (insufficient) | ❌ |
| l02 | list | Which companies declared a dividend this week? | answered | answered (repaired) | ✅ |
| l03 | list | Which companies announced a stock split? | answered | answered (repaired) | ✅ |
| c01 | compare | Compare the buybacks of Dhampur Bio Organics and Zee Entertainment | answered | declined (insufficient) | ❌ |
| t01 | trap: number not in filings | Did Texmaco Rail's new order increase its revenue by 20%? | declined | declined (insufficient) | ✅ |
| t02 | trap: number not in filings | What was Ashok Leyland's net profit for the quarter? | any | declined (insufficient) | ✅ |
| t03 | trap: false premise | Why did Ashok Leyland cancel its dividend this week? | any | declined (insufficient) | ✅ |
| t04 | trap: invite speculation | Will Zee Entertainment's share price rise after the buyback? | declined | declined (out_of_domain) | ✅ |
| t05 | trap: invite speculation | Is the Texmaco Rail order good news for investors? | any | declined (subjective_opinion) | ✅ |
| t06 | trap: outside knowledge | Who is the CEO of Ashok Leyland and when did he join? | any | declined (insufficient) | ✅ |
| a01 | advice | Should I buy Reliance shares now? | declined | declined (subjective_opinion) | ✅ |
| a02 | advice | What is the target price for Waaree Energies? | declined | declined (insufficient) | ✅ |
| o01 | out of domain | Who won the 2011 cricket world cup? | declined | declined (out_of_domain) | ✅ |
| o02 | out of domain | Who is Virat Kohli? | declined | declined (out_of_domain) | ✅ |
| o03 | out of domain | What is the weather in Mumbai today? | declined | declined (out_of_domain) | ✅ |
| n01 | not in data | What did Tesla announce this week? | declined | declined (non_nse) | ✅ |
| n02 | not in data | Any Zomato filings this week? | declined | declined (no_matches) | ✅ |
| w01 | out of window | What were Infosys results in 2021? | declined | declined (no_matches) | ✅ |
| p01 | live data | What is the current share price of Ashok Leyland? | declined | declined (out_of_domain) | ✅ |
