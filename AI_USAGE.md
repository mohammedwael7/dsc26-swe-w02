## Tools
- OpenAI Codex assisted with the initial implementation, error mapping, pagination design, and documentation.

## What AI got wrong
- The workspace did not contain the DSC template, so its pinned dependency file and public tests could not be preserved or inspected. The local Python executable is 3.15.2, while the task requires Python 3.12; FastAPI and pytest are not installed in this environment.
- Review the generated dependency pins and implementation against the actual DSC starter before submission.

## In my own words
- Why does listParcels need a cursor rather than an offset? AI drafted an example answer: an offset counts rows, so when earlier parcels stop matching a state filter, the remaining rows move and a client could miss one; a cursor remembers where it stopped in creation order. Rewrite this in your own words before submission, as the task requires.
- Which of your four operations would break the courier app if you renamed one field, and who would have to approve that change? AI drafted an example answer: changing a field in an operation can break a client that reads or sends it, so the courier app team and API owner should agree before the change ships. Rewrite this in your own words before submission, as the task requires.
